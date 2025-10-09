"""
用户信息意图识别
在用户首次连接时自动检测并处理用户信息
"""

import json
from typing import Dict, Any
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.providers.user.user_info_manager import UserInfoManager
from plugins_func.functions.smart_name_collector import should_ask_for_name, get_name_collection_prompt
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

# 用户信息意图检测函数描述
user_info_intent_function_desc = {
    "type": "function",
    "function": {
        "name": "user_info_intent",
        "description": "检测用户信息状态，如果是新用户或没有姓名则引导用户提供姓名",
        "parameters": {
            "type": "object",
            "properties": {
                "user_input": {
                    "type": "string",
                    "description": "用户的输入内容"
                }
            },
            "required": ["user_input"]
        }
    }
}


@register_function("user_info_intent", user_info_intent_function_desc, ToolType.SYSTEM_CTL)
def user_info_intent(conn, user_input: str):
    """用户信息意图检测和处理 - 已禁用，改为连接时处理"""
    # 用户信息检查已移至WebSocket连接时处理，此函数不再执行问名字逻辑
    logger.bind(tag=TAG).info("user_info_intent函数已禁用，用户信息检查已移至连接时处理")
    return ActionResponse(Action.NONE, "用户信息检查已移至连接时处理", None)


def should_trigger_user_info_check(conn, user_input: str) -> bool:
    """判断是否应该触发用户信息检查"""
    try:
        device_id = conn.device_id
        if not device_id:
            return False
        
        # 检查是否是首次交互
        user_manager = UserInfoManager(conn.config)
        user_info = user_manager.get_user_info(device_id)
        
        if not user_info:
            # 新用户，需要检查
            return True
        
        # 检查是否有姓名
        has_name = user_manager.has_user_name(device_id)
        if not has_name:
            # 没有姓名，需要检查
            return True
        
        # 检查交互次数
        interaction_count = user_info.get("interactionCount", 0)
        if interaction_count <= 3:
            # 前几次交互，可能需要检查
            return True
        
        return False
        
    except Exception as e:
        logger.bind(tag=TAG).error(f"检查是否应该触发用户信息检查失败: {e}")
        return False


def get_user_context_for_llm(conn) -> str:
    """获取用户上下文信息，用于LLM生成更个性化的回复"""
    try:
        device_id = conn.device_id
        if not device_id:
            return ""
        
        user_manager = UserInfoManager(conn.config)
        user_context = user_manager.get_user_context(device_id)
        
        context_parts = []
        
        if user_context.get("user_name"):
            context_parts.append(f"用户姓名：{user_context['user_name']}")
        
        if user_context.get("user_nickname"):
            context_parts.append(f"用户昵称：{user_context['user_nickname']}")
        
        if user_context.get("user_age"):
            context_parts.append(f"用户年龄：{user_context['user_age']}岁")
        
        if user_context.get("interaction_count"):
            context_parts.append(f"交互次数：{user_context['interaction_count']}次")
        
        if user_context.get("knowledge_base"):
            if isinstance(user_context["knowledge_base"], dict):
                for key, value in user_context["knowledge_base"].items():
                    if key != "last_update":
                        context_parts.append(f"{key}：{value}")
            else:
                context_parts.append(f"知识库：{user_context['knowledge_base']}")
        
        if context_parts:
            return "用户信息：\n" + "\n".join(context_parts)
        else:
            return "用户信息：新用户，尚未设置姓名"
            
    except Exception as e:
        logger.bind(tag=TAG).error(f"获取用户上下文失败: {e}")
        return ""

