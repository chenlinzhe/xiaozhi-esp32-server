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
        # 使用与项目中其他地方一致的配置路径
        self.api_base_url = self.config.get("manager_api_url", "http://localhost:8002")
        # Java API的context-path是/xiaozhi，Controller的RequestMapping是/xiaozhi/scenario
        # 所以完整路径是 /xiaozhi + /xiaozhi/scenario = /xiaozhi/xiaozhi/scenario
        # 获取服务器密钥（用于配置API）
        self.server_secret = self.config.get("manager-api", {}).get("secret", "")
        # 用户token（用于场景API）
        self.user_token = None
        self.sessions = {}
        
        # 初始化logger
        from config.logger import setup_logging
        self.logger = setup_logging()
        
        print(f"DialogueService初始化成功，API地址: {self.api_base_url}")
    
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
    
    def _get_user_auth_headers(self) -> Dict[str, str]:
        """获取用户token认证头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # 使用用户token进行认证
        if self.user_token:
            headers["Authorization"] = f"Bearer {self.user_token}"
        return headers
    
    async def _login_and_get_token(self) -> bool:
        """登录并获取用户token"""
        try:
            print("正在登录获取用户token...")
            async with aiohttp.ClientSession() as session:
                # 尝试使用常见的用户名登录
                login_attempts = [
                    {"username": "ningwenjie", "password": "310113Nm."},  # 用户提供的凭据
                ]
                
                for attempt in login_attempts:
                    try:
                        login_data = {
                            "username": attempt["username"],
                            "password": attempt["password"],
                            "captcha": "123456"   # 跳过验证码验证
                        }
                        
                        url = f"{self.api_base_url}/user/login"
                        headers = {"Content-Type": "application/json"}
                        
                        print(f"尝试登录: username={attempt['username']}")
                        async with session.post(url, json=login_data, headers=headers) as response:
                             if response.status == 200:
                                 data = await response.json()
                                 print(f"登录响应数据: {data}")
                                 if data.get('code') == 0:
                                     token_data = data.get('data', {})
                                     # 尝试多种可能的token字段名
                                     self.user_token = (
                                         token_data.get('accessToken') or 
                                         token_data.get('token') or 
                                         token_data.get('access_token') or
                                         data.get('token') or
                                         data.get('accessToken')
                                     )
                                     if self.user_token:
                                         print(f"登录成功，用户: {attempt['username']}, token: {self.user_token[:20]}...")
                                         return True
                                     else:
                                         print(f"登录成功但未获取到token，完整响应: {data}")
                                         continue
                                 else:
                                     print(f"登录失败: {data.get('msg', '未知错误')}")
                                     continue
                             else:
                                 print(f"登录请求失败: HTTP {response.status}")
                                 continue
                    except Exception as e:
                        print(f"登录尝试异常: {e}")
                        continue
                
                print("所有登录尝试都失败了")
                return False
        except Exception as e:
            print(f"登录异常: {e}")
            return False
    
    async def start_scenario(self, session_id: str, scenario_id: str, child_name: str) -> Dict:
        """开始场景对话"""
        try:
            print(f"开始场景对话: session_id={session_id}, scenario_id={scenario_id}, child_name={child_name}")
            
            # 获取场景信息
            print(f"正在获取场景信息: scenario_id={scenario_id}")
            scenario = await self._get_scenario(scenario_id)
            if not scenario:
                print(f"场景不存在: scenario_id={scenario_id}")
                return {"success": False, "error": "场景不存在"}
            
            print(f"获取到场景信息: {scenario.get('scenarioName', 'Unknown')}")
            
            # 获取场景步骤
            print(f"正在获取场景步骤: scenario_id={scenario_id}")
            steps = await self._get_scenario_steps(scenario_id)
            if not steps:
                print(f"场景步骤不存在: scenario_id={scenario_id}")
                return {"success": False, "error": "场景步骤不存在"}
            
            print(f"获取到 {len(steps)} 个场景步骤")
            
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
            
            print(f"创建会话成功: session_id={session_id}")
            
            # 返回第一个步骤
            first_step = steps[0] if steps else {}
            result = {
                "success": True,
                "session_id": session_id,
                "scenario_name": scenario.get("scenarioName", ""),
                "current_step": first_step,
                "total_steps": len(steps)
            }
            
            print(f"场景对话开始成功: {result}")
            return result
            
        except Exception as e:
            print(f"开始场景对话失败: {e}")
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
        
        # 判断是否进入下一步
        if evaluation["score"] >= 60 or evaluation["retry_count"] >= 3:
            # 进入下一步
            session["current_step"] += 1
            if session["current_step"] >= len(session["steps"]):
                # 场景完成
                await self._complete_scenario(session)
                return {
                    "success": True,
                    "action": "completed",
                    "evaluation": evaluation,
                    "final_score": self._calculate_final_score(session)
                }
            else:
                # 下一步
                next_step = session["steps"][session["current_step"]]
                return {
                    "success": True,
                    "action": "next_step",
                    "current_step": next_step,
                    "evaluation": evaluation
                }
        else:
            # 重试当前步骤
            current_step = session["steps"][session["current_step"]]
            
            # 如果有替代消息，使用替代消息
            if evaluation.get("alternative_message"):
                return {
                    "success": True,
                    "action": "retry",
                    "current_step": current_step,
                    "evaluation": evaluation,
                    "ai_message": evaluation["alternative_message"]
                }
            else:
                return {
                    "success": True,
                    "action": "retry",
                    "current_step": current_step,
                    "evaluation": evaluation
                }
    
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
        
        # 获取替代消息
        alternative_message = current_step.get("alternativeMessage", "")
        if alternative_message:
            # 替换儿童姓名占位符
            child_name = session.get("child_name", "小朋友")
            alternative_message = alternative_message.replace("{文杰}", child_name)
        self.logger.info(f"替代消息: {alternative_message}")
        
        # 智能反馈生成
        feedback = self._generate_smart_feedback(base_score, retry_count)
        self.logger.info(f"智能反馈: {feedback}")
        
        result = {
            "score": base_score,
            "feedback": feedback,
            "step_index": session["current_step"],
            "retry_count": retry_count,
            "alternative_message": alternative_message,
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
    
    def _calculate_final_score(self, session: Dict) -> int:
        """计算最终分数"""
        if not session["evaluations"]:
            return 0
        
        total = sum(eval["score"] for eval in session["evaluations"])
        return int(total / len(session["evaluations"]))
    
    async def _get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """获取场景信息"""
        try:
            print(f"正在获取场景信息: scenario_id={scenario_id}")
            
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return None
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/{scenario_id}"
                headers = self._get_user_auth_headers()
                print(f"请求场景信息URL: {url}")
                print(f"请求头: {headers}")
                
                async with session.get(url, headers=headers) as response:
                    print(f"场景信息API响应状态: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"场景信息API响应数据: {data}")
                        
                        # 检查API返回的错误码，与项目中其他地方保持一致
                        if data.get('code') == 0:
                            scenario = data.get("data")
                            if scenario:
                                print(f"获取到场景信息: {scenario.get('scenarioName', 'Unknown')}")
                                print("\n=== 场景详细信息 ===")
                                print(f"场景ID: {scenario.get('scenarioId', 'N/A')}")
                                print(f"场景名称: {scenario.get('scenarioName', 'N/A')}")
                                print(f"描述: {scenario.get('description', 'N/A')}")
                                print(f"是否活跃: {scenario.get('isActive', False)}")
                                print(f"创建时间: {scenario.get('createdAt', 'N/A')}")
                                print(f"更新时间: {scenario.get('updatedAt', 'N/A')}")
                                print(f"完整数据: {scenario}")
                            else:
                                print("没有获取到场景信息数据")
                            return scenario
                        else:
                            print(f"API返回错误: {data.get('msg', '未知错误')}")
                            return None
                    else:
                        print(f"获取场景信息失败: HTTP {response.status}")
                        return None
        except Exception as e:
            print(f"获取场景信息失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _get_scenario_steps(self, scenario_id: str) -> List[Dict]:
        """获取场景步骤"""
        try:
            print(f"正在获取场景步骤: scenario_id={scenario_id}")
            
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return []
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario-step/list/{scenario_id}"
                headers = self._get_user_auth_headers()
                print(f"请求场景步骤URL: {url}")
                print(f"请求头: {headers}")
                
                async with session.get(url, headers=headers) as response:
                    print(f"场景步骤API响应状态: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"场景步骤API响应数据: {data}")
                        
                        # 检查API返回的错误码，与项目中其他地方保持一致
                        if data.get('code') == 0:
                            steps = data.get("data", [])
                            print(f"获取到 {len(steps)} 个场景步骤")
                            
                            # 详细输出步骤数据
                            print("\n=== 场景步骤详细信息 ===")
                            for i, step in enumerate(steps):
                                print(f"\n步骤 {i+1}:")
                                print(f"  步骤ID: {step.get('stepId', 'N/A')}")
                                print(f"  步骤名称: {step.get('stepName', 'N/A')}")
                                print(f"  步骤顺序: {step.get('stepOrder', 'N/A')}")
                                print(f"  AI消息: {step.get('aiMessage', 'N/A')}")
                                print(f"  期望关键词: {step.get('expectedKeywords', 'N/A')}")
                                print(f"  替代提示: {step.get('alternativeMessage', 'N/A')}")
                                print(f"  是否活跃: {step.get('isActive', False)}")
                                print(f"  创建时间: {step.get('createdAt', 'N/A')}")
                                print(f"  更新时间: {step.get('updatedAt', 'N/A')}")
                                print(f"  完整数据: {step}")
                            
                            return steps
                        else:
                            print(f"API返回错误: {data.get('msg', '未知错误')}")
                            return []
                    else:
                        print(f"获取场景步骤失败: HTTP {response.status}")
                        return []
        except Exception as e:
            print(f"获取场景步骤失败: {e}")
            import traceback
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
                url = f"{self.api_base_url}/xiaozhi/learning-record"
                headers = self._get_server_auth_headers()
                await session_client.post(url, json=record_data, headers=headers)
                
        except Exception as e:
            print(f"完成场景失败: {e}")
    
    async def get_scenarios(self) -> List[Dict]:
        """获取场景列表"""
        try:
            print(f"正在获取场景列表，API地址: {self.api_base_url}")
            
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return []
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/list"
                params = {"page": 1, "limit": 100}
                headers = self._get_user_auth_headers()
                print(f"请求URL: {url}, 参数: {params}")
                print(f"请求头: {headers}")
                
                async with session.get(url, params=params, headers=headers) as response:
                    print(f"场景列表API响应状态: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"场景列表API响应数据: {data}")
                        
                        # 检查API返回的错误码，与项目中其他地方保持一致
                        if data.get('code') == 0:
                            scenarios = data.get("data", {}).get("list", [])
                            active_scenarios = [s for s in scenarios if s.get("isActive", False)]
                            print(f"获取到 {len(scenarios)} 个场景，其中 {len(active_scenarios)} 个活跃场景")
                            
                            # 详细输出场景数据
                            print("\n=== 场景详细信息 ===")
                            for i, scenario in enumerate(scenarios):
                                print(f"\n场景 {i+1}:")
                                print(f"  数据库ID: {scenario.get('id', 'N/A')}")
                                print(f"  场景ID: {scenario.get('scenarioId', 'N/A')}")
                                print(f"  场景名称: {scenario.get('scenarioName', 'N/A')}")
                                print(f"  是否活跃: {scenario.get('isActive', False)}")
                                print(f"  描述: {scenario.get('description', 'N/A')}")
                                print(f"  创建时间: {scenario.get('createDate', 'N/A')}")
                                print(f"  更新时间: {scenario.get('updateDate', 'N/A')}")
                                print(f"  完整数据: {scenario}")
                            
                            return active_scenarios
                        else:
                            print(f"API返回错误: {data.get('msg', '未知错误')}")
                            return []
                    else:
                        print(f"获取场景列表失败: HTTP {response.status}")
                        return []
        except Exception as e:
            print(f"获取场景列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_default_teaching_scenario(self) -> Optional[Dict]:
        """获取默认教学场景"""
        try:
            print(f"正在获取默认教学场景，API地址: {self.api_base_url}")
            
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return None
            
            async with aiohttp.ClientSession() as session:
                # 通过查询is_default_teaching=1来获取默认教学场景
                url = f"{self.api_base_url}/xiaozhi/scenario/list"
                params = {"page": 1, "limit": 100, "isDefaultTeaching": 1}
                headers = self._get_user_auth_headers()
                print(f"请求URL: {url}, 参数: {params}")
                print(f"请求头: {headers}")
                
                async with session.get(url, params=params, headers=headers) as response:
                    print(f"默认教学场景API响应状态: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"默认教学场景API响应数据: {data}")
                        
                        # 检查API返回的错误码，与项目中其他地方保持一致
                        if data.get('code') == 0:
                            scenarios = data.get("data", {}).get("list", [])
                            # 查找is_default_teaching=1的场景
                            default_scenarios = [s for s in scenarios if s.get("isDefaultTeaching", 0) == 1]
                            
                            if default_scenarios:
                                default_scenario = default_scenarios[0]  # 取第一个默认教学场景
                                print(f"获取到默认教学场景: {default_scenario.get('scenarioName', 'Unknown')}")
                                print("\n=== 默认教学场景详细信息 ===")
                                print(f"场景ID: {default_scenario.get('scenarioId', 'N/A')}")
                                print(f"场景名称: {default_scenario.get('scenarioName', 'N/A')}")
                                print(f"描述: {default_scenario.get('description', 'N/A')}")
                                print(f"是否活跃: {default_scenario.get('isActive', False)}")
                                print(f"创建时间: {default_scenario.get('createDate', 'N/A')}")
                                print(f"更新时间: {default_scenario.get('updateDate', 'N/A')}")
                                print(f"完整数据: {default_scenario}")
                                return default_scenario
                            else:
                                print("没有找到默认教学场景")
                                return None
                        else:
                            print(f"API返回错误: {data.get('msg', '未知错误')}")
                            return None
                    else:
                        print(f"获取默认教学场景失败: HTTP {response.status}")
                        return None
        except Exception as e:
            print(f"获取默认教学场景失败: {e}")
            import traceback
            traceback.print_exc()
            return None
