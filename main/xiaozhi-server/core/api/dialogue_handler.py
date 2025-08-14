"""
对话API处理器
"""

import json
import uuid
from typing import Dict, Any
from core.scenario.dialogue_service import DialogueService


class DialogueHandler:
    """对话处理器"""
    
    def __init__(self):
        self.dialogue_service = DialogueService()
    
    async def handle_dialogue_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理对话请求"""
        try:
            action = request_data.get("action")
            
            if action == "start_scenario":
                return await self._handle_start_scenario(request_data)
            elif action == "process_response":
                return await self._handle_process_response(request_data)
            elif action == "get_scenarios":
                return await self._handle_get_scenarios(request_data)
            elif action == "free_chat":
                return await self._handle_free_chat(request_data)
            else:
                return {"success": False, "error": "未知操作"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_start_scenario(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理开始场景请求"""
        scenario_id = request_data.get("scenario_id")
        child_name = request_data.get("child_name", "小朋友")
        
        if not scenario_id:
            return {"success": False, "error": "场景ID不能为空"}
        
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 开始场景对话
        result = await self.dialogue_service.start_scenario(session_id, scenario_id, child_name)
        
        if result["success"]:
            return {
                "success": True,
                "session_id": session_id,
                "scenario_name": result["scenario_name"],
                "current_step": result["current_step"],
                "total_steps": result["total_steps"],
                "message": f"开始学习场景：{result['scenario_name']}",
                "ai_message": result["current_step"].get("aiMessage", "你好！")
            }
        else:
            return result
    
    async def _handle_process_response(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户回复"""
        session_id = request_data.get("session_id")
        user_text = request_data.get("user_text")
        
        if not session_id or not user_text:
            return {"success": False, "error": "会话ID和用户文本不能为空"}
        
        # 处理回复
        result = await self.dialogue_service.process_response(session_id, user_text)
        
        if result["success"]:
            action = result["action"]
            evaluation = result["evaluation"]
            
            if action == "next_step":
                return {
                    "success": True,
                    "action": "next_step",
                    "session_id": session_id,
                    "ai_message": result["current_step"].get("aiMessage", "很好！"),
                    "evaluation": evaluation,
                    "message": f"进入下一步：{evaluation['feedback']}"
                }
            elif action == "retry":
                return {
                    "success": True,
                    "action": "retry",
                    "session_id": session_id,
                    "ai_message": result["current_step"].get("aiMessage", "再试一次"),
                    "evaluation": evaluation,
                    "message": f"重试：{evaluation['feedback']}"
                }
            elif action == "completed":
                return {
                    "success": True,
                    "action": "completed",
                    "session_id": session_id,
                    "final_score": result["final_score"],
                    "evaluation": evaluation,
                    "message": f"场景学习完成！最终得分：{result['final_score']}分"
                }
        else:
            return result
    
    async def _handle_get_scenarios(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取场景列表"""
        scenarios = await self.dialogue_service.get_scenarios()
        
        return {
            "success": True,
            "scenarios": scenarios,
            "message": f"获取到 {len(scenarios)} 个可用场景"
        }
    
    async def _handle_free_chat(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理自由聊天"""
        user_text = request_data.get("user_text", "")
        child_name = request_data.get("child_name", "小朋友")
        
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
