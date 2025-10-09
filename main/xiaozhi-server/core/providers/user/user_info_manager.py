"""
用户信息管理器
负责管理设备绑定的用户信息，包括姓名收集和知识库管理
"""

import json
import requests
from typing import Optional, Dict, Any
from config.logger import setup_logging
from config.manage_api_client import ManageApiClient

TAG = __name__
logger = setup_logging()


class UserInfoManager:
    """用户信息管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger
        
    def get_user_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        try:
            if not ManageApiClient._instance:
                self.logger.bind(tag=TAG).error("ManageApiClient未初始化")
                return None
                
            result = ManageApiClient._instance._execute_request(
                "GET",
                "/user/info",
                params={"deviceId": device_id}
            )
            return result
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"获取用户信息失败: {e}")
            return None
    
    def has_user_name(self, device_id: str) -> bool:
        """检查用户是否已设置姓名"""
        try:
            if not ManageApiClient._instance:
                self.logger.bind(tag=TAG).error("ManageApiClient未初始化")
                return False
                
            result = ManageApiClient._instance._execute_request(
                "GET",
                "/user/has-name",
                params={"deviceId": device_id}
            )
            return result if result is not None else False
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"检查用户姓名失败: {e}")
            return False
    
    def update_user_name(self, device_id: str, user_name: str) -> bool:
        """更新用户姓名"""
        try:
            if not ManageApiClient._instance:
                self.logger.bind(tag=TAG).error("ManageApiClient未初始化")
                return False
                
            result = ManageApiClient._instance._execute_request(
                "POST",
                "/user/update-name",
                json={
                    "deviceId": device_id,
                    "userName": user_name
                }
            )
            return result if result is not None else False
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"更新用户姓名失败: {e}")
            return False
    
    def update_knowledge_base(self, device_id: str, knowledge_base: str) -> bool:
        """更新用户知识库"""
        try:
            if not ManageApiClient._instance:
                self.logger.bind(tag=TAG).error("ManageApiClient未初始化")
                return False
                
            result = ManageApiClient._instance._execute_request(
                "POST",
                "/user/update-knowledge",
                json={
                    "deviceId": device_id,
                    "knowledgeBase": knowledge_base
                }
            )
            return result if result is not None else False
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"更新用户知识库失败: {e}")
            return False
    
    def get_knowledge_base(self, device_id: str) -> Optional[str]:
        """获取用户知识库"""
        try:
            if not ManageApiClient._instance:
                self.logger.bind(tag=TAG).error("ManageApiClient未初始化")
                return None
                
            result = ManageApiClient._instance._execute_request(
                "GET",
                "/user/knowledge",
                params={"deviceId": device_id}
            )
            return result
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"获取用户知识库失败: {e}")
            return None
    
    def record_interaction(self, device_id: str, interaction_type: str, 
                          user_input: str, ai_response: str) -> bool:
        """记录用户交互"""
        try:
            if not ManageApiClient._instance:
                self.logger.bind(tag=TAG).error("ManageApiClient未初始化")
                return False
                
            result = ManageApiClient._instance._execute_request(
                "POST",
                "/user/interaction",
                json={
                    "deviceId": device_id,
                    "interactionType": interaction_type,
                    "userInput": user_input,
                    "aiResponse": ai_response
                }
            )
            return result if result is not None else False
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"记录用户交互失败: {e}")
            return False
    
    def get_user_context(self, device_id: str) -> Dict[str, Any]:
        """获取用户上下文信息，用于增强AI回复"""
        user_info = self.get_user_info(device_id)
        knowledge_base = self.get_knowledge_base(device_id)
        
        context = {
            "has_name": False,
            "user_name": None,
            "knowledge_base": None
        }
        
        if user_info:
            context["has_name"] = bool(user_info.get("userName"))
            context["user_name"] = user_info.get("userName")
            context["user_nickname"] = user_info.get("userNickname")
            context["user_age"] = user_info.get("userAge")
            context["user_gender"] = user_info.get("userGender")
            context["interaction_count"] = user_info.get("interactionCount", 0)
        
        if knowledge_base:
            try:
                context["knowledge_base"] = json.loads(knowledge_base)
            except json.JSONDecodeError:
                context["knowledge_base"] = knowledge_base
        
        return context

