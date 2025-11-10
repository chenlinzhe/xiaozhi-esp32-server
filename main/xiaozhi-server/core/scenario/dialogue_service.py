"""
场景对话服务
"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
from config.config_loader import load_config


class DialogueService:
    """对话服务"""
    
    def __init__(self):
        self.config = load_config()
        # 使用配置文件中的manager-api.url，如果不存在则使用默认值
        manager_api_config = self.config.get("manager-api", {})
        self.api_base_url = manager_api_config.get("url", "http://localhost:8002")
        # 获取服务器密钥（用于配置API）
        self.server_secret = manager_api_config.get("secret", "")
        self.sessions = {}
        
        # 初始化logger
        from config.logger import setup_logging
        self.logger = setup_logging()
    
    def _get_server_auth_headers(self) -> Dict[str, str]:
        """获取服务器密钥认证头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # 使用服务器密钥进行认证，与manage_api_client.py保持一致
        if self.server_secret and "你" not in self.server_secret:
            headers["Authorization"] = f"Bearer {self.server_secret}"
        return headers
    

    
    async def start_scenario(self, session_id: str, scenario_id: str, child_name: str) -> Dict:
        """开始场景对话"""
        try:
            print(f"=== 开始场景对话调试 ===")
            print(f"会话ID: {session_id}")
            print(f"场景ID: {scenario_id}")
            print(f"儿童姓名: {child_name}")
            
            # 获取场景信息
            print(f"正在获取场景信息: {scenario_id}")
            scenario = await self._get_scenario(scenario_id)
            print(f"场景获取结果: {scenario}")
            
            # 如果单个场景获取失败，尝试从场景列表中获取
            if not scenario:
                print(f"单个场景获取失败，尝试从场景列表中获取: {scenario_id}")
                scenarios = self.get_scenarios()
                if scenarios:
                    for s in scenarios:
                        if str(s.get('id')) == str(scenario_id):
                            scenario = s
                            print(f"从场景列表中找到匹配的场景: {scenario}")
                            break
                
                if not scenario:
                    print(f"场景不存在: {scenario_id}")
                    return {"success": False, "error": "场景不存在"}
            
            print(f"场景信息详情:")
            print(f"  - 场景ID: {scenario.get('id', 'N/A')}")
            print(f"  - 场景名称: {scenario.get('scenarioName', 'N/A')}")
            # print(f"  - 是否活跃: {scenario.get('isActive', 'N/A')}")
            # print(f"  - 代理ID: {scenario.get('agentId', 'N/A')}")
            
            # 获取场景步骤
            print(f"正在获取场景步骤: {scenario_id}")
            steps = await self._get_scenario_steps(scenario_id)
            # print(f"步骤获取结果: {steps}")
            
            if not steps:
                print(f"场景步骤不存在，创建默认步骤: {scenario_id}")
                # 创建默认步骤
                steps = [{
                    "id": "default_step_1",
                    "stepName": "默认步骤",
                    "stepOrder": 1,
                    "aiMessage": f"你好，{child_name}！欢迎开始学习。",
                    "expectedKeywords": '["你好", "开始", "学习"]',
                    "alternativeMessage": "让我们开始学习吧！",
                    "timeoutSeconds": 20,
                    "scenarioId": scenario_id
                }]
                print(f"创建了默认步骤: {steps}")
            
            # print(f"步骤信息详情:")
            # print(f"  - 步骤数量: {len(steps)}")
            # for i, step in enumerate(steps):
            #     print(f"  - 步骤 {i+1}:")
            #     print(f"    * 步骤ID: {step.get('id', 'N/A')}")
            #     print(f"    * 步骤名称: {step.get('stepName', 'N/A')}")
            #     print(f"    * 步骤顺序: {step.get('stepOrder', 'N/A')}")
            #     print(f"    * AI消息: {step.get('aiMessage', 'N/A')}")
            
            # 创建会话
            self.sessions[session_id] = {
                "scenario_id": scenario_id,
                "child_name": child_name,
                "scenario": scenario,
                "steps": steps,
                "current_step": 0,
                "start_time": datetime.now(),
                "evaluations": []
            }
            
            # 返回第一个步骤
            first_step = steps[0] if steps else {}
            # 处理步骤的消息列表
            messages = self._process_step_messages(first_step, child_name)
            result = {
                "success": True,
                "session_id": session_id,
                "scenario_name": scenario.get("scenarioName", ""),
                "current_step": first_step,
                "messages": messages,
                "total_steps": len(steps)
            }
            
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def process_response(self, session_id: str, user_text: str) -> Dict:
        """处理用户回复"""
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "会话不存在"}
        
        # 评估回复
        evaluation = self._evaluate_response(session, user_text)
        session["evaluations"].append(evaluation)
        
        # 根据匹配程度决定分支跳转
        return await self._handle_step_branches(session, evaluation)
    
    def _evaluate_response(self, session: Dict, user_text: str) -> Dict:
        """评估用户回复 - 优化版本"""
        self.logger.info(f"=== 开始评估用户回复 ===")
        self.logger.info(f"用户输入: {user_text}")
        self.logger.info(f"会话数据: {session}")
        
        current_step = session["steps"][session["current_step"]]
        self.logger.info(f"当前步骤: {current_step}")
        
        # 处理期望关键词 - API返回的是JSON字符串，需要解析
        expected_keywords_str = current_step.get("expectedKeywords", "")
        self.logger.info(f"期望关键词原始字符串: {expected_keywords_str}")
        
        expected_keywords = []
        if expected_keywords_str:
            try:
                import json
                expected_keywords = json.loads(expected_keywords_str)
                self.logger.info(f"JSON解析成功，期望关键词: {expected_keywords}")
            except (json.JSONDecodeError, TypeError) as e:
                self.logger.warning(f"JSON解析失败: {e}，尝试按逗号分割")
                # 如果解析失败，尝试按逗号分割
                expected_keywords = [kw.strip() for kw in expected_keywords_str.split(",") if kw.strip()]
                self.logger.info(f"逗号分割结果: {expected_keywords}")
        
        # 智能关键词匹配（支持模糊匹配）
        matches = 0
        total_keywords = len(expected_keywords) if expected_keywords else 1
        self.logger.info(f"开始关键词匹配，总关键词数: {total_keywords}")
        
        for keyword in expected_keywords:
            keyword_clean = keyword.strip().lower()
            user_text_clean = user_text.lower()
            
            self.logger.info(f"检查关键词: '{keyword_clean}' vs 用户输入: '{user_text_clean}'")
            
            # 精确匹配
            if keyword_clean in user_text_clean:
                matches += 1
                self.logger.info(f"精确匹配成功: '{keyword_clean}'")
            # 模糊匹配（关键词包含在用户回答中）
            elif any(kw in user_text_clean for kw in keyword_clean.split()):
                matches += 0.8
                self.logger.info(f"模糊匹配成功: '{keyword_clean}'")
            # 语义相似度匹配（简单实现）
            elif self._check_semantic_similarity(keyword_clean, user_text_clean):
                matches += 0.6
                self.logger.info(f"语义相似度匹配成功: '{keyword_clean}'")
            else:
                self.logger.info(f"关键词 '{keyword_clean}' 未匹配")
        
        self.logger.info(f"匹配结果: {matches}/{total_keywords}")
        
        # 计算分数
        base_score = int((matches / total_keywords) * 100)
        self.logger.info(f"基础分数计算: {matches}/{total_keywords} * 100 = {base_score}")
        
        # 计算重试次数
        retry_count = 0
        if "evaluations" in session:
            for eval in session["evaluations"]:
                if eval.get("step_index") == session["current_step"]:
                    retry_count += 1
        self.logger.info(f"重试次数: {retry_count}")
        
        # 根据重试次数调整分数
        if retry_count > 0:
            # 重试时给予鼓励性加分
            encouragement_bonus = min(retry_count * 5, 20)
            base_score = min(base_score + encouragement_bonus, 100)
            self.logger.info(f"重试加分: +{encouragement_bonus}, 最终分数: {base_score}")
        
        # 直接走成功条件分支配置
        self.logger.info(f"使用成功条件分支配置进行跳转")
        
        # 智能反馈生成
        feedback = self._generate_smart_feedback(base_score, retry_count)
        self.logger.info(f"智能反馈: {feedback}")
        
        result = {
            "score": base_score,
            "feedback": feedback,
            "step_index": session["current_step"],
            "retry_count": retry_count,
            "is_excellent": base_score >= 90,
            "is_good": base_score >= 80,
            "is_pass": base_score >= 60
        }
        
        self.logger.info(f"评估结果: {result}")
        self.logger.info(f"是否优秀: {result['is_excellent']}")
        self.logger.info(f"是否良好: {result['is_good']}")
        self.logger.info(f"是否及格: {result['is_pass']}")
        
        return result
    
    def _check_semantic_similarity(self, keyword: str, user_text: str) -> bool:
        """检查语义相似度（简单实现）"""
        # 同义词映射
        synonyms = {
            "渴了": ["口渴", "想喝水", "需要水"],
            "饿了": ["肚子饿", "想吃东西", "需要食物"],
            "谢谢": ["感谢", "谢谢", "多谢"],
            "对不起": ["抱歉", "不好意思", "对不起"]
        }
        
        if keyword in synonyms:
            return any(syn in user_text for syn in synonyms[keyword])
        
        return False
    
    def _generate_smart_feedback(self, score: int, retry_count: int) -> str:
        """生成智能反馈"""
        import random
        
        self.logger.info(f"=== 生成智能反馈 ===")
        self.logger.info(f"分数: {score}")
        self.logger.info(f"重试次数: {retry_count}")
        
        if score >= 90:
            praise_messages = [
                "太棒了！你说得很好！",
                "真聪明！回答得非常好！",
                "哇！你真是太厉害了！",
                "完美！你学得很快！"
            ]
            feedback = random.choice(praise_messages)
            self.logger.info(f"优秀级别反馈: {feedback}")
        elif score >= 80:
            good_messages = [
                "很好！回答得很棒！",
                "不错！你说得对！",
                "真棒！继续加油！",
                "很好！你理解得很清楚！"
            ]
            feedback = random.choice(good_messages)
            self.logger.info(f"良好级别反馈: {feedback}")
        elif score >= 60:
            pass_messages = [
                "不错！再试试看。",
                "加油！你可以做得更好。",
                "很好！再努力一下。",
                "不错！继续努力！"
            ]
            feedback = random.choice(pass_messages)
            self.logger.info(f"及格级别反馈: {feedback}")
        else:
            if retry_count > 0:
                encouragement_messages = [
                    "没关系，我们再试一次！",
                    "加油，你可以的！",
                    "别着急，慢慢来~",
                    "再想想看，我相信你！"
                ]
                feedback = random.choice(encouragement_messages)
                self.logger.info(f"重试鼓励反馈: {feedback}")
            else:
                feedback = "没关系，我们再试一次！"
                self.logger.info(f"默认反馈: {feedback}")
        
        return feedback
    
    def _process_step_messages(self, step: Dict, child_name: str) -> List[str]:
        """处理步骤的消息列表 - 只处理消息列表，不再处理AI消息
        
        Args:
            step: 步骤配置
            child_name: 儿童姓名
            
        Returns:
            List[str]: 消息列表
        """
        messages = []
        
        # 只检查消息列表配置
        message_list = step.get("messageList", [])
        if message_list and isinstance(message_list, list):
            self.logger.info(f"使用消息列表，消息数量: {len(message_list)}")
            for msg in message_list:
                if isinstance(msg, str) and msg.strip():
                    # 替换儿童姓名占位符
                    msg = msg.replace("{文杰}", child_name)
                    msg = msg.replace("{childName}", child_name)
                    messages.append(msg)
            return messages
        
        # 如果没有消息列表，返回空列表
        self.logger.info(f"没有配置消息列表")
        return messages
    
    async def _handle_step_branches(self, session: Dict, evaluation: Dict) -> Dict:
        """处理步骤的三分支逻辑
        
        Args:
            session: 会话数据
            evaluation: 评估结果
            
        Returns:
            Dict: 处理结果
        """
        current_step = session["steps"][session["current_step"]]
        score = evaluation["score"]
        retry_count = evaluation["retry_count"]
        
        self.logger.info(f"=== 处理步骤分支逻辑 ===")
        self.logger.info(f"当前分数: {score}")
        self.logger.info(f"重试次数: {retry_count}")
        
        # 1. 完全匹配分支 (分数 >= 90)
        if score >= 90:
            self.logger.info("完全匹配分支")
            return self._handle_perfect_match_branch(session, current_step, evaluation)
        
        # 2. 部分匹配分支 (60 <= 分数 < 90)
        elif score >= 60:
            self.logger.info("部分匹配分支")
            return self._handle_partial_match_branch(session, current_step, evaluation)
        
        # 3. 完全不匹配分支 (分数 < 60)
        else:
            self.logger.info("完全不匹配分支")
            return await self._handle_no_match_branch(session, current_step, evaluation)
    
    def _handle_perfect_match_branch(self, session: Dict, current_step: Dict, evaluation: Dict) -> Dict:
        """处理完全匹配分支"""
        # 检查是否有完全匹配的下一步配置
        perfect_match_next_step_id = current_step.get("perfectMatchNextStepId")
        
        if perfect_match_next_step_id:
            # 跳转到完全匹配的指定步骤
            next_step_index = self._find_step_by_id(session["steps"], perfect_match_next_step_id)
            if next_step_index is not None:
                session["current_step"] = next_step_index
                next_step = session["steps"][next_step_index]
                messages = self._process_step_messages(next_step, session["child_name"])
                return {
                    "success": True,
                    "action": "perfect_match_next",
                    "current_step": next_step,
                    "messages": messages,
                    "evaluation": evaluation,
                    "branch_type": "perfect_match"
                }
        
        # 默认进入下一步
        return self._handle_default_next_step(session, evaluation)
    
    def _handle_partial_match_branch(self, session: Dict, current_step: Dict, evaluation: Dict) -> Dict:
        """处理部分匹配分支"""
        # 检查是否有部分匹配的下一步配置
        partial_match_next_step_id = current_step.get("partialMatchNextStepId")
        
        if partial_match_next_step_id:
            # 跳转到部分匹配的指定步骤
            next_step_index = self._find_step_by_id(session["steps"], partial_match_next_step_id)
            if next_step_index is not None:
                session["current_step"] = next_step_index
                next_step = session["steps"][next_step_index]
                messages = self._process_step_messages(next_step, session["child_name"])
                return {
                    "success": True,
                    "action": "partial_match_next",
                    "current_step": next_step,
                    "messages": messages,
                    "evaluation": evaluation,
                    "branch_type": "partial_match"
                }
        
        # 默认进入下一步
        return self._handle_default_next_step(session, evaluation)
    
    async def _handle_no_match_branch(self, session: Dict, current_step: Dict, evaluation: Dict) -> Dict:
        """处理完全不匹配分支"""
        # 检查是否有完全不匹配的下一步配置
        no_match_next_step_id = current_step.get("noMatchNextStepId")
        
        if no_match_next_step_id:
            # 跳转到完全不匹配的指定步骤
            next_step_index = self._find_step_by_id(session["steps"], no_match_next_step_id)
            if next_step_index is not None:
                session["current_step"] = next_step_index
                next_step = session["steps"][next_step_index]
                messages = self._process_step_messages(next_step, session["child_name"])
                return {
                    "success": True,
                    "action": "no_match_next",
                    "current_step": next_step,
                    "messages": messages,
                    "evaluation": evaluation,
                    "branch_type": "no_match"
                }
        
        # 检查重试次数
        if evaluation["retry_count"] >= 3:
            # 重试次数用完，强制进入下一步
            return await self._handle_default_next_step(session, evaluation)
        else:
            # 重试当前步骤
            return self._handle_retry_current_step(session, current_step, evaluation)
    
    async def _handle_default_next_step(self, session: Dict, evaluation: Dict) -> Dict:
        """处理默认的下一步逻辑"""
        # 获取当前步骤的鼓励词（在进入下一步前）
        current_step_index = session["current_step"]
        if current_step_index < len(session["steps"]):
            current_step = session["steps"][current_step_index]
            encouragement_words = current_step.get('encouragementWords', '')
        else:
            encouragement_words = ''
        
        session["current_step"] += 1
        if session["current_step"] >= len(session["steps"]):
            # 场景完成
            await self._complete_scenario(session)
            return {
                "success": True,
                "action": "completed",
                "evaluation": evaluation,
                "final_score": self._calculate_final_score(session),
                "encouragement_words": encouragement_words
            }
        else:
            # 下一步
            next_step = session["steps"][session["current_step"]]
            messages = self._process_step_messages(next_step, session["child_name"])
            
            # 如果有鼓励词，添加到消息中
            if encouragement_words:
                # 在消息列表的开头添加鼓励词
                encouragement_message = {
                    "content": encouragement_words,
                    "speechRate": 1.0,
                    "waitTimeSeconds": 2,
                    "messageType": "encouragement"
                }
                messages.insert(0, encouragement_message)
            
            return {
                "success": True,
                "action": "next_step",
                "current_step": next_step,
                "messages": messages,
                "evaluation": evaluation,
                "encouragement_words": encouragement_words
            }
    
    def _handle_retry_current_step(self, session: Dict, current_step: Dict, evaluation: Dict) -> Dict:
        """处理重试当前步骤"""
        # 不再使用替代消息，直接处理步骤的消息列表
        messages = self._process_step_messages(current_step, session["child_name"])
        return {
            "success": True,
            "action": "retry",
            "current_step": current_step,
            "messages": messages,
            "evaluation": evaluation
        }
    
    def _find_step_by_id(self, steps: List[Dict], step_id: str) -> Optional[int]:
        """根据步骤ID查找步骤索引"""
        for i, step in enumerate(steps):
            if step.get("id") == step_id:
                return i
        return None
    
    def _calculate_final_score(self, session: Dict) -> int:
        """计算最终分数"""
        if not session["evaluations"]:
            return 0
        
        total = sum(eval["score"] for eval in session["evaluations"])
        return int(total / len(session["evaluations"]))
    
    async def _get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """获取场景信息"""
        try:
            print(f"=== _get_scenario 调试 ===")
            print(f"场景ID: {scenario_id}")
            
            async with aiohttp.ClientSession() as session:
                # 配置文件中的URL已经包含了/xiaozhi路径，所以这里只需要添加/scenario/{scenario_id}
                url = f"{self.api_base_url}/scenario/{scenario_id}"
                headers = self._get_server_auth_headers()
                print(f"请求URL: {url}")
                print(f"请求头: {headers}")
                
                async with session.get(url, headers=headers) as response:
                    print(f"响应状态码: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        # print(f"响应数据: {data}")
                        
                        # 检查API返回的错误码，与项目中其他地方保持一致
                        if data.get('code') == 0:
                            scenario = data.get("data")
                            # print(f"获取到场景数据: {scenario}")
                            
                            # 详细打印场景数据
                            # if scenario:
                            #     print(f"\n=== 详细场景数据 ===")
                            #     print(f"  - 场景ID: {scenario.get('id', 'N/A')}")
                            #     print(f"  - 场景名称: {scenario.get('scenarioName', 'N/A')}")
                            #     print(f"  - 是否活跃: {scenario.get('isActive', 'N/A')}")
                            #     print(f"  - 代理ID: {scenario.get('agentId', 'N/A')}")
                            #     print(f"  - 是否默认教学: {scenario.get('isDefaultTeaching', 'N/A')}")
                            #     print(f"  - 创建时间: {scenario.get('createTime', 'N/A')}")
                            #     print(f"  - 更新时间: {scenario.get('updateTime', 'N/A')}")
                            #     print(f"  - 完整场景数据: {scenario}")
                            
                            return scenario
                        else:
                            print(f"API返回错误码: {data.get('code')}, 错误信息: {data.get('message', 'N/A')}")
                            return None
                    else:
                        print(f"HTTP请求失败，状态码: {response.status}")
                        response_text = await response.text()
                        print(f"响应内容: {response_text}")
                        return None
        except Exception as e:
            print(f"_get_scenario 异常: {e}")
            traceback.print_exc()
            return None
    
    async def _get_scenario_steps(self, scenario_id: str) -> List[Dict]:
        """获取场景步骤"""
        try:
            # print(f"=== _get_scenario_steps 调试 ===")
            # print(f"场景ID: {scenario_id}")
            
            async with aiohttp.ClientSession() as session:
                # 配置文件中的URL已经包含了/xiaozhi路径，所以这里只需要添加/scenario-step/list/{scenario_id}
                url = f"{self.api_base_url}/scenario-step/list/{scenario_id}"
                headers = self._get_server_auth_headers()
                print(f"请求URL: {url}")
                print(f"请求头: {headers}")
                
                async with session.get(url, headers=headers) as response:
                    print(f"响应状态码: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        # print(f"响应数据: {data}")
                        
                        # 检查API返回的错误码，与项目中其他地方保持一致
                        if data.get('code') == 0:
                            steps = data.get("data", [])
                            # print(f"获取到步骤数据: {steps}")
                            # print(f"步骤数量: {len(steps)}")
                            
                            # 详细打印每个步骤的数据
                            print(f"\n=== 详细步骤数据 ===")
                            for i, step in enumerate(steps):
                                print(f"\n步骤 {i+1}:")
                                # print(f"  - 步骤ID: {step.get('id', 'N/A')}")
                                # print(f"  - 步骤名称: {step.get('stepName', 'N/A')}")
                                # print(f"  - 步骤顺序: {step.get('stepOrder', 'N/A')}")
                                # print(f"  - AI消息: {step.get('aiMessage', 'N/A')}")
                                # print(f"  - 使用消息列表: {step.get('useMessageList', 'N/A')}")
                                # print(f"  - 消息列表配置: {step.get('messageListConfig', 'N/A')}")
                                # print(f"  - 期望关键词: {step.get('expectedKeywords', 'N/A')}")
                                # print(f"  - 替代消息: {step.get('alternativeMessage', 'N/A')}")
                                # print(f"  - 超时时间: {step.get('timeoutSeconds', 'N/A')}")
                                # print(f"  - 场景ID: {step.get('scenarioId', 'N/A')}")
                                # print(f"  - 创建时间: {step.get('createTime', 'N/A')}")
                                # print(f"  - 更新时间: {step.get('updateTime', 'N/A')}")
                                # print(f"  - 在_get_scenario_steps 完整步骤数据: {step}")
                            
                            return steps
                        else:
                            print(f"API返回错误码: {data.get('code')}, 错误信息: {data.get('message', 'N/A')}")
                            return []
                    else:
                        print(f"HTTP请求失败，状态码: {response.status}")
                        response_text = await response.text()
                        print(f"响应内容: {response_text}")
                        return []
        except Exception as e:
            print(f"_get_scenario_steps 异常: {e}")
            traceback.print_exc()
            return []
    
    async def _complete_scenario(self, session: Dict):
        """完成场景"""
        try:
            final_score = self._calculate_final_score(session)
            
            # 保存学习记录
            record_data = {
                "scenario_id": session["scenario_id"],
                "child_name": session["child_name"],
                "success_rate": final_score,
                "learning_duration": (datetime.now() - session["start_time"]).total_seconds(),
                "created_at": datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session_client:
                # 配置文件中的URL已经包含了/xiaozhi路径，所以这里只需要添加/learning-record
                url = f"{self.api_base_url}/learning-record"
                headers = self._get_server_auth_headers()
                await session_client.post(url, json=record_data, headers=headers)
                
        except Exception as e:
            pass
    
    def get_scenarios(self) -> List[Dict]:
        """获取场景列表"""
        try:
            print(f"=== get_scenarios 调试 ===")
            from config.manage_api_client import get_scenario_list
            result = get_scenario_list(page=1, limit=100, is_active=True)
            # print(f"API调用结果: {result}")
            
            if result:
                scenarios = result.get("list", [])
                # print(f"原始场景列表: {scenarios}")
                active_scenarios = [s for s in scenarios if s.get("isActive", False)]
                # print(f"活跃场景列表: {active_scenarios}")
                
                # print(f"\n=== 详细场景数据 ===")
                # for i, scenario in enumerate(active_scenarios):
                #     print(f"\n活跃场景 {i+1}:")
                #     print(f"  - 场景ID: {scenario.get('id', 'N/A')}")
                #     print(f"  - 场景名称: {scenario.get('scenarioName', 'N/A')}")
                #     print(f"  - 是否活跃: {scenario.get('isActive', 'N/A')}")
                #     print(f"  - 代理ID: {scenario.get('agentId', 'N/A')}")
                #     print(f"  - 是否默认教学: {scenario.get('isDefaultTeaching', 'N/A')}")
                #     print(f"  - 创建时间: {scenario.get('createTime', 'N/A')}")
                #     print(f"  - 更新时间: {scenario.get('updateTime', 'N/A')}")
                #     print(f"  - 完整场景数据: {scenario}")
                
                return active_scenarios
            else:
                print("API返回None或空结果")
                return []
        except Exception as e:
            print(f"get_scenarios 异常: {e}")
            traceback.print_exc()
            return []
    
    def get_default_teaching_scenario(self) -> Optional[Dict]:
        """获取默认教学场景"""
        try:
            from config.manage_api_client import get_scenario_list
            result = get_scenario_list(page=1, limit=100)
            if result:
                scenarios = result.get("list", [])
                # 查找is_default_teaching=1的场景
                default_scenarios = [s for s in scenarios if s.get("isDefaultTeaching", 0) == 1]
                
                if default_scenarios:
                    default_scenario = default_scenarios[0]  # 取第一个默认教学场景
                    return default_scenario
                else:
                    return None
            else:
                return None
        except Exception as e:
            traceback.print_exc()
            return None
