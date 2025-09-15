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
    """用户信息意图检测和处理"""
    try:
        device_id = conn.device_id
        if not device_id:
            logger.bind(tag=TAG).error("设备ID为空，无法处理用户信息意图")
            return ActionResponse(Action.ERROR, "设备ID为空", "无法处理用户信息意图")
        
        # 初始化用户信息管理器
        user_manager = UserInfoManager(conn.config)
        
        # 检查用户是否已有姓名
        has_name = user_manager.has_user_name(device_id)
        
        if not has_name:
            # 用户没有姓名，需要收集
            logger.bind(tag=TAG).info(f"用户 {device_id} 没有姓名，开始收集流程")
            
            # 检查用户输入是否包含姓名信息
            from plugins_func.functions.smart_name_collector import extract_name_from_input, is_valid_name
            
            extracted_name = extract_name_from_input(user_input)
            
            if extracted_name and is_valid_name(extracted_name):
                # 用户输入包含姓名，直接保存
                success = user_manager.update_user_name(device_id, extracted_name)
                
                if success:
                    welcome_message = f"很高兴认识你，{extracted_name}！我已经记住了你的名字。从现在开始，我会用这个名字来称呼你。有什么我可以帮助你的吗？"
                    logger.bind(tag=TAG).info(f"从用户输入中收集到姓名: {extracted_name}")
                    
                    # 记录交互
                    user_manager.record_interaction(device_id, "name_collection", user_input, welcome_message)
                    
                    return ActionResponse(Action.RESPONSE, welcome_message, welcome_message)
                else:
                    error_message = "抱歉，保存你的姓名时出现了问题，请稍后再试。"
                    logger.bind(tag=TAG).error(f"保存用户 {device_id} 姓名失败")
                    return ActionResponse(Action.ERROR, "保存失败", error_message)
            else:
                # 用户输入不包含姓名，询问姓名
                name_prompt = get_name_collection_prompt()
                logger.bind(tag=TAG).info(f"用户 {device_id} 输入不包含姓名，询问姓名")
                
                # 记录交互
                user_manager.record_interaction(device_id, "name_request", user_input, name_prompt)
                
                return ActionResponse(Action.RESPONSE, name_prompt, name_prompt)
        else:
            # 用户已有姓名，获取用户信息并正常处理
            user_info = user_manager.get_user_info(device_id)
            user_name = user_info.get("userName") if user_info else "朋友"
            
            # 记录交互
            user_manager.record_interaction(device_id, "normal_interaction", user_input, "")
            
            # 返回继续聊天的指示
            return ActionResponse(Action.NONE, "用户已有姓名，继续正常对话", None)
            
    except Exception as e:
        logger.bind(tag=TAG).error(f"用户信息意图处理失败: {e}")
        return ActionResponse(Action.ERROR, str(e), "处理用户信息时出现错误")


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

