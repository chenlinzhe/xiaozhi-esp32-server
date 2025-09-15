"""
用户信息管理功能
包括用户信息检测、姓名收集和知识库管理
"""

import json
import re
from typing import Dict, Any
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.providers.user.user_info_manager import UserInfoManager
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

# 用户信息检测函数描述
check_user_info_function_desc = {
    "type": "function",
    "function": {
        "name": "check_user_info",
        "description": "检测设备绑定的用户信息，如果没有用户姓名，则询问用户姓名",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

# 收集用户姓名函数描述
collect_user_name_function_desc = {
    "type": "function",
    "function": {
        "name": "collect_user_name",
        "description": "收集并保存用户的姓名信息",
        "parameters": {
            "type": "object",
            "properties": {
                "user_name": {
                    "type": "string",
                    "description": "用户提供的姓名"
                }
            },
            "required": ["user_name"]
        }
    }
}

# 更新用户知识库函数描述
update_knowledge_base_function_desc = {
    "type": "function",
    "function": {
        "name": "update_knowledge_base",
        "description": "更新用户的知识库信息，记录用户的相关信息",
        "parameters": {
            "type": "object",
            "properties": {
                "knowledge_info": {
                    "type": "string",
                    "description": "要添加到知识库的信息"
                }
            },
            "required": ["knowledge_info"]
        }
    }
}

# 获取用户信息函数描述
get_user_info_function_desc = {
    "type": "function",
    "function": {
        "name": "get_user_info",
        "description": "获取当前用户的基本信息和知识库",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


@register_function("check_user_info", check_user_info_function_desc, ToolType.SYSTEM_CTL)
def check_user_info(conn):
    """检测用户信息，如果没有姓名则询问"""
    try:
        device_id = conn.device_id
        if not device_id:
            logger.bind(tag=TAG).error("设备ID为空，无法检测用户信息")
            return ActionResponse(Action.ERROR, "设备ID为空", "无法检测用户信息")
        
        # 初始化用户信息管理器
        user_manager = UserInfoManager(conn.config)
        
        # 检查用户是否已有姓名
        has_name = user_manager.has_user_name(device_id)
        
        if not has_name:
            # 用户没有姓名，询问姓名
            greeting_message = "你好！我是小智，很高兴认识你！请问你叫什么名字呢？"
            logger.bind(tag=TAG).info(f"用户 {device_id} 没有姓名，询问姓名")
            
            # 记录交互
            user_manager.record_interaction(device_id, "greeting", "", greeting_message)
            
            return ActionResponse(Action.RESPONSE, greeting_message, greeting_message)
        else:
            # 用户已有姓名，获取用户信息
            user_info = user_manager.get_user_info(device_id)
            user_name = user_info.get("userName") if user_info else "朋友"
            
            greeting_message = f"你好 {user_name}！很高兴再次见到你！有什么我可以帮助你的吗？"
            logger.bind(tag=TAG).info(f"用户 {device_id} 已有姓名: {user_name}")
            
            # 记录交互
            user_manager.record_interaction(device_id, "greeting", "", greeting_message)
            
            return ActionResponse(Action.RESPONSE, greeting_message, greeting_message)
            
    except Exception as e:
        logger.bind(tag=TAG).error(f"检测用户信息失败: {e}")
        return ActionResponse(Action.ERROR, str(e), "检测用户信息时出现错误")


@register_function("collect_user_name", collect_user_name_function_desc, ToolType.SYSTEM_CTL)
def collect_user_name(conn, user_name: str):
    """收集并保存用户姓名"""
    try:
        device_id = conn.device_id
        if not device_id:
            logger.bind(tag=TAG).error("设备ID为空，无法保存用户姓名")
            return ActionResponse(Action.ERROR, "设备ID为空", "无法保存用户姓名")
        
        if not user_name or not user_name.strip():
            return ActionResponse(Action.ERROR, "用户名为空", "请提供有效的姓名")
        
        # 清理用户名
        clean_name = user_name.strip()
        
        # 初始化用户信息管理器
        user_manager = UserInfoManager(conn.config)
        
        # 保存用户姓名
        success = user_manager.update_user_name(device_id, clean_name)
        
        if success:
            welcome_message = f"很高兴认识你，{clean_name}！我已经记住了你的名字。从现在开始，我会用这个名字来称呼你。有什么我可以帮助你的吗？"
            logger.bind(tag=TAG).info(f"成功保存用户 {device_id} 的姓名: {clean_name}")
            
            # 记录交互
            user_manager.record_interaction(device_id, "name_collection", user_name, welcome_message)
            
            return ActionResponse(Action.RESPONSE, welcome_message, welcome_message)
        else:
            error_message = "抱歉，保存你的姓名时出现了问题，请稍后再试。"
            logger.bind(tag=TAG).error(f"保存用户 {device_id} 姓名失败")
            return ActionResponse(Action.ERROR, "保存失败", error_message)
            
    except Exception as e:
        logger.bind(tag=TAG).error(f"收集用户姓名失败: {e}")
        return ActionResponse(Action.ERROR, str(e), "收集姓名时出现错误")


@register_function("update_knowledge_base", update_knowledge_base_function_desc, ToolType.SYSTEM_CTL)
def update_knowledge_base(conn, knowledge_info: str):
    """更新用户知识库"""
    try:
        device_id = conn.device_id
        if not device_id:
            logger.bind(tag=TAG).error("设备ID为空，无法更新知识库")
            return ActionResponse(Action.ERROR, "设备ID为空", "无法更新知识库")
        
        if not knowledge_info or not knowledge_info.strip():
            return ActionResponse(Action.ERROR, "知识库信息为空", "请提供有效的信息")
        
        # 初始化用户信息管理器
        user_manager = UserInfoManager(conn.config)
        
        # 获取现有知识库
        existing_knowledge = user_manager.get_knowledge_base(device_id)
        
        # 解析现有知识库
        knowledge_dict = {}
        if existing_knowledge:
            try:
                knowledge_dict = json.loads(existing_knowledge)
            except json.JSONDecodeError:
                # 如果不是JSON格式，作为普通文本处理
                knowledge_dict = {"general_info": existing_knowledge}
        
        # 添加新信息
        knowledge_dict["last_update"] = knowledge_info
        
        # 保存更新后的知识库
        updated_knowledge = json.dumps(knowledge_dict, ensure_ascii=False)
        success = user_manager.update_knowledge_base(device_id, updated_knowledge)
        
        if success:
            confirm_message = "好的，我已经记住了这个信息。"
            logger.bind(tag=TAG).info(f"成功更新用户 {device_id} 的知识库")
            
            # 记录交互
            user_manager.record_interaction(device_id, "knowledge_update", knowledge_info, confirm_message)
            
            return ActionResponse(Action.RESPONSE, confirm_message, confirm_message)
        else:
            error_message = "抱歉，保存信息时出现了问题，请稍后再试。"
            logger.bind(tag=TAG).error(f"更新用户 {device_id} 知识库失败")
            return ActionResponse(Action.ERROR, "保存失败", error_message)
            
    except Exception as e:
        logger.bind(tag=TAG).error(f"更新知识库失败: {e}")
        return ActionResponse(Action.ERROR, str(e), "更新知识库时出现错误")


@register_function("get_user_info", get_user_info_function_desc, ToolType.SYSTEM_CTL)
def get_user_info(conn):
    """获取用户信息"""
    try:
        device_id = conn.device_id
        if not device_id:
            logger.bind(tag=TAG).error("设备ID为空，无法获取用户信息")
            return ActionResponse(Action.ERROR, "设备ID为空", "无法获取用户信息")
        
        # 初始化用户信息管理器
        user_manager = UserInfoManager(conn.config)
        
        # 获取用户上下文信息
        user_context = user_manager.get_user_context(device_id)
        
        # 构建用户信息摘要
        info_summary = "用户信息：\n"
        
        if user_context.get("user_name"):
            info_summary += f"姓名：{user_context['user_name']}\n"
        
        if user_context.get("user_nickname"):
            info_summary += f"昵称：{user_context['user_nickname']}\n"
        
        if user_context.get("user_age"):
            info_summary += f"年龄：{user_context['user_age']}岁\n"
        
        if user_context.get("user_gender"):
            gender_map = {0: "未知", 1: "男", 2: "女"}
            info_summary += f"性别：{gender_map.get(user_context['user_gender'], '未知')}\n"
        
        if user_context.get("interaction_count"):
            info_summary += f"交互次数：{user_context['interaction_count']}次\n"
        
        if user_context.get("knowledge_base"):
            if isinstance(user_context["knowledge_base"], dict):
                info_summary += "知识库信息：\n"
                for key, value in user_context["knowledge_base"].items():
                    if key != "last_update":
                        info_summary += f"  - {key}: {value}\n"
            else:
                info_summary += f"知识库：{user_context['knowledge_base']}\n"
        
        if not user_context.get("user_name"):
            info_summary += "注意：用户尚未设置姓名\n"
        
        logger.bind(tag=TAG).info(f"获取用户 {device_id} 信息成功")
        
        # 记录交互
        user_manager.record_interaction(device_id, "info_query", "", info_summary)
        
        return ActionResponse(Action.REQLLM, info_summary, None)
        
    except Exception as e:
        logger.bind(tag=TAG).error(f"获取用户信息失败: {e}")
        return ActionResponse(Action.ERROR, str(e), "获取用户信息时出现错误")


def extract_name_from_text(text: str) -> str:
    """从文本中提取可能的姓名"""
    if not text:
        return ""
    
    # 移除常见的称呼和语气词
    text = re.sub(r'^(我叫|我的名字是|我是|你可以叫我)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[，。！？,\.\!\?]', '', text)
    text = text.strip()
    
    # 如果包含多个词，取前两个词作为姓名
    words = text.split()
    if len(words) > 2:
        return ' '.join(words[:2])
    elif len(words) == 1:
        return words[0]
    else:
        return text

