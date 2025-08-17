"""
聊天状态管理器
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from core.utils.redis_client import get_redis_client
from core.scenario.dialogue_service import DialogueService
from config.logger import setup_logging


class ChatStatusManager:
    """聊天状态管理器"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.redis_client = get_redis_client()
        self.dialogue_service = DialogueService()
        
        # 模式切换关键词
        self.TEACHING_MODE_KEYWORDS = ["切换到教学模式", "教学模式", "开始教学"]
        self.FREE_MODE_KEYWORDS = ["切换到自由模式", "自由模式", "自由聊天"]
        
        # 等待时间配置（秒）
        self.WAIT_TIME_MIN = 5
        self.WAIT_TIME_MAX = 10
        
        # 智能评估配置
        self.ASSESSMENT_CONFIG = {
            "excellent_threshold": 90,  # 优秀阈值
            "good_threshold": 80,       # 良好阈值
            "pass_threshold": 60,       # 及格阈值
            "max_retries": 3,           # 最大重试次数
            "encouragement_messages": [
                "没关系，我们再试一次！",
                "加油，你可以的！",
                "别着急，慢慢来~",
                "再想想看，我相信你！"
            ],
            "praise_messages": [
                "太棒了！你说得很好！",
                "真聪明！回答得非常好！",
                "哇！你真是太厉害了！",
                "完美！你学得很快！"
            ]
        }
    
    def is_mode_switch_command(self, user_text: str) -> Optional[str]:
        """判断是否为模式切换命令
        
        Args:
            user_text: 用户输入的文本
            
        Returns:
            str: 目标模式 ("teaching_mode" 或 "free_mode")，如果不是切换命令返回None
        """
        user_text = user_text.strip()
        self.logger.debug(f"判断是否为模式切换命令: {user_text}")
        
        if any(keyword in user_text for keyword in self.TEACHING_MODE_KEYWORDS):
            self.logger.info(f"检测到教学模式切换命令: {user_text}")
            return "teaching_mode"
        elif any(keyword in user_text for keyword in self.FREE_MODE_KEYWORDS):
            self.logger.info(f"检测到自由模式切换命令: {user_text}")
            return "free_mode"
        
        return None
    
    def set_user_chat_status(self, user_id: str, status: str) -> bool:
        """设置用户聊天状态
        
        Args:
            user_id: 用户ID
            status: 聊天状态
            
        Returns:
            bool: 设置是否成功
        """
        return self.redis_client.set_chat_status(user_id, status)
    
    def get_user_chat_status(self, user_id: str) -> str:
        """获取用户聊天状态，默认为自由模式
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 聊天状态
        """
        status = self.redis_client.get_chat_status(user_id)
        return status if status else "free_mode"
    
    async def handle_user_input(self, user_id: str, user_text: str, 
                               child_name: str = "小朋友") -> Dict[str, Any]:
        """处理用户输入
        
        Args:
            user_id: 用户ID
            user_text: 用户输入的文本
            child_name: 儿童姓名
            
        Returns:
            Dict: 处理结果
        """
        try:
            self.logger.info(f"处理用户输入: user_id={user_id}, user_text={user_text[:50]}..., child_name={child_name}")
            
            # 检查是否为模式切换命令
            target_mode = self.is_mode_switch_command(user_text)
            if target_mode:
                self.logger.info(f"检测到模式切换命令: {target_mode}")
                # 切换模式
                success = self.set_user_chat_status(user_id, target_mode)
                if not success:
                    self.logger.error(f"设置用户 {user_id} 聊天状态失败")
                    return {
                        "success": False,
                        "error": "设置聊天状态失败"
                    }
                
                if target_mode == "teaching_mode":
                    self.logger.info("切换到教学模式，开始教学会话")
                    # 切换到教学模式时，直接开始教学会话并输出场景第一句话
                    return await self._start_teaching_session(user_id, child_name, from_mode_switch=True)
                else:
                    self.logger.info("切换到自由模式")
                    return {
                        "success": True,
                        "action": "mode_switch", 
                        "mode": "free_mode",
                        "ai_message": f"好的，{child_name}！现在进入自由聊天模式，我们可以随意聊天了。",
                        "message": "已切换到自由模式"
                    }
            
            # 获取当前聊天状态
            current_status = self.get_user_chat_status(user_id)
            self.logger.info(f"用户 {user_id} 当前聊天状态: {current_status}")
            
            if current_status == "teaching_mode":
                self.logger.info("当前为教学模式，处理教学逻辑")
                return await self._handle_teaching_mode(user_id, user_text, child_name)
            else:
                self.logger.info("当前为自由模式，继续正常流程")
                return await self._handle_free_mode(user_text, child_name)
                
        except Exception as e:
            self.logger.error(f"处理用户输入失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"处理用户输入失败: {str(e)}"
            }
    
    async def _handle_teaching_mode(self, user_id: str, user_text: str, 
                                   child_name: str) -> Dict[str, Any]:
        """处理教学模式
        
        Args:
            user_id: 用户ID
            user_text: 用户输入的文本
            child_name: 儿童姓名
            
        Returns:
            Dict: 处理结果
        """
        self.logger.info(f"处理教学模式: user_id={user_id}, user_text={user_text}, child_name={child_name}")
        
        # 获取或创建教学会话
        session_data = self.redis_client.get_session_data(f"teaching_{user_id}")
        
        if not session_data:
            self.logger.info("没有找到现有教学会话，创建新的教学会话")
            # 创建新的教学会话
            return await self._start_teaching_session(user_id, child_name)
        else:
            self.logger.info(f"找到现有教学会话: {session_data}")
            # 处理教学会话中的用户回复
            return await self._process_teaching_response(user_id, user_text, session_data, child_name)
    
    async def _start_teaching_session(self, user_id: str, child_name: str, from_mode_switch: bool = False) -> Dict[str, Any]:
        """开始教学会话
        
        Args:
            user_id: 用户ID
            child_name: 儿童姓名
            from_mode_switch: 是否从模式切换开始
            
        Returns:
            Dict: 处理结果
        """
        try:
            self.logger.info(f"开始教学会话: user_id={user_id}, child_name={child_name}, from_mode_switch={from_mode_switch}")
            
            # 获取默认教学场景
            self.logger.info("正在获取默认教学场景...")
            default_scenario = await self.dialogue_service.get_default_teaching_scenario()
            if default_scenario:
                self.logger.info(f"获取到默认教学场景: {default_scenario.get('scenarioName', 'Unknown')}")
            else:
                self.logger.warning("没有获取到默认教学场景，尝试获取第一个可用场景")
                # 如果没有默认教学场景，获取第一个可用场景
                scenarios = await self.dialogue_service.get_scenarios()
                self.logger.info(f"获取到 {len(scenarios) if scenarios else 0} 个场景")
                
                if not scenarios or len(scenarios) == 0:
                    self.logger.error("没有可用的教学场景")
                    return {
                        "success": False,
                        "error": "没有可用的教学场景，请联系管理员配置教学场景"
                    }
                default_scenario = scenarios[0]
                self.logger.info(f"使用第一个场景: {default_scenario.get('scenarioName', 'Unknown')}")
            
            # 使用数据库ID而不是scenarioId，因为API期望数字ID
            scenario_id = default_scenario.get("id")
            if not scenario_id:
                self.logger.error("场景配置错误，缺少场景ID")
                return {
                    "success": False,
                    "error": "场景配置错误，缺少场景ID"
                }
            
            self.logger.info(f"开始场景对话: scenario_id={scenario_id}")
            # 开始场景对话
            result = await self.dialogue_service.start_scenario(
                f"teaching_{user_id}", scenario_id, child_name
            )
            
            self.logger.info(f"场景对话结果: {result}")
            
            if result["success"]:
                # 保存会话数据
                session_data = {
                    "session_id": result["session_id"],
                    "scenario_id": scenario_id,
                    "scenario_name": result["scenario_name"],
                    "current_step": 0,
                    "total_steps": result["total_steps"],
                    "start_time": time.time(),
                    "waiting_for_response": True,
                    "wait_start_time": time.time(),
                    "evaluations": [] # 新增评估结果列表
                }
                
                self.logger.info(f"保存会话数据: {session_data}")
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                
                # 根据是否从模式切换开始，返回不同的action
                if from_mode_switch:
                    response = {
                        "success": True,
                        "action": "mode_switch",
                        "mode": "teaching_mode",
                        "session_id": result["session_id"],
                        "scenario_name": result["scenario_name"],
                        "ai_message": result["current_step"].get("aiMessage", f"你好，{child_name}！"),
                        "message": f"已切换到教学模式，开始学习场景：{result['scenario_name']}",
                        "wait_time": 0  # 立即开始，不等待
                    }
                else:
                    response = {
                        "success": True,
                        "action": "start_teaching",
                        "session_id": result["session_id"],
                        "scenario_name": result["scenario_name"],
                        "ai_message": result["current_step"].get("aiMessage", f"你好，{child_name}！"),
                        "message": f"开始学习场景：{result['scenario_name']}",
                        "wait_time": self.WAIT_TIME_MAX
                    }
                
                self.logger.info(f"教学会话开始成功: {response}")
                return response
            else:
                self.logger.error(f"场景对话失败: {result}")
                return result
                
        except Exception as e:
            self.logger.error(f"开始教学会话失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"开始教学会话失败: {str(e)}"
            }
    
    async def _process_teaching_response(self, user_id: str, user_text: str, 
                                        session_data: Dict[str, Any], 
                                        child_name: str) -> Dict[str, Any]:
        """处理教学回复 - 优化版本"""
        try:
            # 获取当前步骤信息
            scenario_id = session_data.get("scenario_id")
            current_step_index = session_data.get("current_step", 0)
            
            # 获取场景步骤
            steps = await self.dialogue_service._get_scenario_steps(scenario_id)
            if not steps or current_step_index >= len(steps):
                return {
                    "success": False,
                    "error": "场景步骤配置错误"
                }
            
            current_step = steps[current_step_index]
            
            # 智能评估用户回复
            evaluation = self.dialogue_service._evaluate_response(session_data, user_text)
            score = evaluation["score"]
            
            # 记录评估结果
            session_data["evaluations"].append(evaluation)
            
            # 根据评估结果决定下一步
            if evaluation["is_excellent"] or evaluation["is_good"]:
                # 优秀或良好，进入下一步
                session_data["current_step"] += 1
                session_data["waiting_for_response"] = False
                
                # 检查是否完成所有步骤
                if session_data["current_step"] >= len(steps):
                    # 教学完成
                    final_score = self.dialogue_service._calculate_final_score(session_data)
                    session_data["completed"] = True
                    session_data["final_score"] = final_score
                    
                    # 保存会话数据
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    
                    # 生成完成消息
                    completion_message = self._generate_completion_message(final_score, child_name)
                    
                    return {
                        "success": True,
                        "action": "completed",
                        "session_id": f"teaching_{user_id}",
                        "ai_message": completion_message,
                        "final_score": final_score,
                        "evaluation": evaluation,
                        "message": f"教学完成！最终得分：{final_score}分"
                    }
                else:
                    # 进入下一步
                    next_step = steps[session_data["current_step"]]
                    ai_message = next_step.get("aiMessage", "")
                    if ai_message:
                        ai_message = ai_message.replace("{文杰}", child_name)
                    
                    # 保存会话数据
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    
                    return {
                        "success": True,
                        "action": "next_step",
                        "session_id": f"teaching_{user_id}",
                        "ai_message": ai_message,
                        "current_step": next_step,
                        "evaluation": evaluation,
                        "message": f"进入下一步：{evaluation['feedback']}",
                        "timeoutSeconds": self.WAIT_TIME_MAX
                    }
            else:
                # 需要重试
                retry_count = evaluation["retry_count"]
                
                # 检查是否超过最大重试次数
                if retry_count >= self.ASSESSMENT_CONFIG["max_retries"]:
                    # 超过重试次数，使用替代消息
                    alternative_message = evaluation.get("alternative_message", "")
                    if not alternative_message:
                        alternative_message = "让我来告诉你正确答案。"
                    
                    # 进入下一步（跳过当前步骤）
                    session_data["current_step"] += 1
                    session_data["waiting_for_response"] = False
                    
                    # 保存会话数据
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    
                    return {
                        "success": True,
                        "action": "next_step",
                        "session_id": f"teaching_{user_id}",
                        "ai_message": alternative_message,
                        "evaluation": evaluation,
                        "message": "使用替代消息继续",
                        "timeoutSeconds": self.WAIT_TIME_MAX
                    }
                else:
                    # 继续重试当前步骤
                    session_data["waiting_for_response"] = False
                    
                    # 保存会话数据
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    
                    # 使用替代消息或原消息重试
                    retry_message = evaluation.get("alternative_message", "")
                    if not retry_message:
                        retry_message = current_step.get("aiMessage", "")
                        if retry_message:
                            retry_message = retry_message.replace("{文杰}", child_name)
                    
                    return {
                        "success": True,
                        "action": "retry",
                        "session_id": f"teaching_{user_id}",
                        "ai_message": retry_message,
                        "current_step": current_step,
                        "evaluation": evaluation,
                        "message": f"重试：{evaluation['feedback']}",
                        "timeoutSeconds": self.WAIT_TIME_MAX
                    }
                    
        except Exception as e:
            self.logger.error(f"处理教学回复失败: {e}")
            return {
                "success": False,
                "error": f"处理教学回复失败: {str(e)}"
            }
    
    def _generate_completion_message(self, final_score: int, child_name: str) -> str:
        """生成教学完成消息"""
        if final_score >= 90:
            return f"太棒了，{child_name}！你完成了所有的学习任务，表现非常优秀！"
        elif final_score >= 80:
            return f"很好，{child_name}！你完成了学习任务，表现很棒！"
        elif final_score >= 60:
            return f"不错，{child_name}！你完成了学习任务，继续加油！"
        else:
            return f"没关系，{child_name}！学习是一个过程，下次会更好的！"
    
    async def _handle_free_mode(self, user_text: str, child_name: str) -> Dict[str, Any]:
        """处理自由模式
        
        Args:
            user_text: 用户输入的文本
            child_name: 儿童姓名
            
        Returns:
            Dict: 处理结果，自由模式下返回None让正常流程继续
        """
        # 自由模式下，不进行特殊处理，让正常的LLM对话流程继续
        return None
    
    async def check_teaching_timeout(self, user_id: str) -> Optional[Dict[str, Any]]:
        """检查教学会话是否超时
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 超时处理结果，如果没有超时返回None
        """
        session_data = self.redis_client.get_session_data(f"teaching_{user_id}")
        
        if not session_data or not session_data.get("waiting_for_response"):
            return None
        
        wait_start_time = session_data.get("wait_start_time", 0)
        current_time = time.time()
        wait_duration = current_time - wait_start_time
        
        # 检查是否超过等待时间
        if wait_duration >= self.WAIT_TIME_MAX:
            # 超时，获取当前步骤的替代消息
            scenario_id = session_data.get("scenario_id")
            current_step = session_data.get("current_step", 0)
            
            # 获取当前步骤的详细信息
            steps = await self.dialogue_service._get_scenario_steps(scenario_id)
            if steps and current_step < len(steps):
                current_step_data = steps[current_step]
                # 优先使用auto_reply_on_timeout，如果没有则使用alternative_message
                timeout_message = (
                    current_step_data.get("autoReplyOnTimeout") or 
                    current_step_data.get("alternativeMessage") or 
                    "时间到了，让我来回答这个问题。"
                )
                
                # 替换儿童姓名占位符
                child_name = session_data.get("child_name", "小朋友")
                if timeout_message:
                    timeout_message = timeout_message.replace("{文杰}", child_name)
                else:
                    timeout_message = "时间到了，让我来回答这个问题。"
            else:
                timeout_message = "时间到了，让我来回答这个问题。"
            
            # 更新会话状态
            session_data["waiting_for_response"] = False
            self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
            
            return {
                "success": True,
                "action": "timeout_response",
                "ai_message": timeout_message,
                "message": "用户超时，使用替代消息回复"
            }
        
        return None
