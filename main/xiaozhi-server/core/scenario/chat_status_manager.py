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
    
    def is_mode_switch_command(self, user_text: str) -> Optional[str]:
        """判断是否为模式切换命令
        
        Args:
            user_text: 用户输入的文本
            
        Returns:
            str: 目标模式 ("teaching_mode" 或 "free_mode")，如果不是切换命令返回None
        """
        user_text = user_text.strip()
        print('判断是否为模式切换命令')
        if any(keyword in user_text for keyword in self.TEACHING_MODE_KEYWORDS):
            return "teaching_mode"
        elif any(keyword in user_text for keyword in self.FREE_MODE_KEYWORDS):
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
        print("处理用户输入")
        # 检查是否为模式切换命令
        target_mode = self.is_mode_switch_command(user_text)
        if target_mode:
            # 切换模式
            self.set_user_chat_status(user_id, target_mode)
            
            if target_mode == "teaching_mode":
                return {
                    "success": True,
                    "action": "mode_switch",
                    "mode": "teaching_mode",
                    "ai_message": f"好的，{child_name}！现在进入教学模式。让我为你选择一个学习场景。",
                    "message": "已切换到教学模式"
                }
            else:
                return {
                    "success": True,
                    "action": "mode_switch", 
                    "mode": "free_mode",
                    "ai_message": f"好的，{child_name}！现在进入自由聊天模式，我们可以随意聊天了。",
                    "message": "已切换到自由模式"
                }
        
        # 获取当前聊天状态
        current_status = self.get_user_chat_status(user_id)
        
        if current_status == "teaching_mode":
            return await self._handle_teaching_mode(user_id, user_text, child_name)
        else:
            return await self._handle_free_mode(user_text, child_name)
    
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
        # 获取或创建教学会话
        session_data = self.redis_client.get_session_data(f"teaching_{user_id}")
        
        if not session_data:
            # 创建新的教学会话
            return await self._start_teaching_session(user_id, child_name)
        else:
            # 处理教学会话中的用户回复
            return await self._process_teaching_response(user_id, user_text, session_data, child_name)
    
    async def _start_teaching_session(self, user_id: str, child_name: str) -> Dict[str, Any]:
        """开始教学会话
        
        Args:
            user_id: 用户ID
            child_name: 儿童姓名
            
        Returns:
            Dict: 处理结果
        """
        try:
            # 获取默认教学场景
            default_scenario = await self.dialogue_service.get_default_teaching_scenario()
            if not default_scenario:
                # 如果没有默认教学场景，获取第一个可用场景
                scenarios = await self.dialogue_service.get_scenarios()
                if not scenarios:
                    return {
                        "success": False,
                        "error": "没有可用的教学场景"
                    }
                default_scenario = scenarios[0]
            
            scenario_id = default_scenario.get("scenarioId")
            
            # 开始场景对话
            result = await self.dialogue_service.start_scenario(
                f"teaching_{user_id}", scenario_id, child_name
            )
            
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
                    "wait_start_time": time.time()
                }
                
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                
                return {
                    "success": True,
                    "action": "start_teaching",
                    "session_id": result["session_id"],
                    "scenario_name": result["scenario_name"],
                    "ai_message": result["current_step"].get("aiMessage", f"你好，{child_name}！"),
                    "message": f"开始学习场景：{result['scenario_name']}",
                    "wait_time": self.WAIT_TIME_MAX
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"开始教学会话失败: {e}")
            return {
                "success": False,
                "error": f"开始教学会话失败: {str(e)}"
            }
    
    async def _process_teaching_response(self, user_id: str, user_text: str, 
                                        session_data: Dict[str, Any], 
                                        child_name: str) -> Dict[str, Any]:
        """处理教学会话中的用户回复
        
        Args:
            user_id: 用户ID
            user_text: 用户输入的文本
            session_data: 会话数据
            child_name: 儿童姓名
            
        Returns:
            Dict: 处理结果
        """
        try:
            session_id = session_data["session_id"]
            
            # 处理回复
            result = await self.dialogue_service.process_response(session_id, user_text)
            
            if result["success"]:
                action = result["action"]
                evaluation = result["evaluation"]
                
                if action == "next_step":
                    # 进入下一步
                    session_data["current_step"] += 1
                    session_data["waiting_for_response"] = True
                    session_data["wait_start_time"] = time.time()
                    
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    
                    return {
                        "success": True,
                        "action": "next_step",
                        "ai_message": result["current_step"].get("aiMessage", "很好！"),
                        "evaluation": evaluation,
                        "message": f"进入下一步：{evaluation['feedback']}",
                        "wait_time": self.WAIT_TIME_MAX
                    }
                    
                elif action == "retry":
                    # 重试当前步骤
                    session_data["waiting_for_response"] = True
                    session_data["wait_start_time"] = time.time()
                    
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    
                    return {
                        "success": True,
                        "action": "retry",
                        "ai_message": result["current_step"].get("aiMessage", "再试一次"),
                        "evaluation": evaluation,
                        "message": f"重试：{evaluation['feedback']}",
                        "wait_time": self.WAIT_TIME_MAX
                    }
                    
                elif action == "completed":
                    # 场景完成，切换到自由模式
                    self.set_user_chat_status(user_id, "free_mode")
                    self.redis_client.delete_session_data(f"teaching_{user_id}")
                    
                    return {
                        "success": True,
                        "action": "completed",
                        "mode": "free_mode",
                        "final_score": result["final_score"],
                        "evaluation": evaluation,
                        "ai_message": f"太棒了，{child_name}！你完成了学习！现在我们可以自由聊天了。",
                        "message": f"场景学习完成！最终得分：{result['final_score']}分"
                    }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"处理教学回复失败: {e}")
            return {
                "success": False,
                "error": f"处理教学回复失败: {str(e)}"
            }
    
    async def _handle_free_mode(self, user_text: str, child_name: str) -> Dict[str, Any]:
        """处理自由模式
        
        Args:
            user_text: 用户输入的文本
            child_name: 儿童姓名
            
        Returns:
            Dict: 处理结果
        """
        # 简单的自由聊天回复
        responses = [
            f"你好，{child_name}！很高兴和你聊天！",
            f"{child_name}，你今天过得怎么样？",
            f"真棒！{child_name}，你还有什么想说的吗？",
            f"我明白了，{child_name}。继续告诉我更多吧！",
            f"{child_name}，你的想法很有趣呢！"
        ]
        
        import random
        ai_message = random.choice(responses)
        
        return {
            "success": True,
            "action": "free_chat",
            "ai_message": ai_message,
            "message": "自由聊天模式"
        }
    
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
            # 超时，自动回复
            session_data["waiting_for_response"] = False
            self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
            
            return {
                "success": True,
                "action": "timeout_response",
                "ai_message": "时间到了，让我来回答这个问题。",
                "message": "用户超时，自动回复"
            }
        
        return None
