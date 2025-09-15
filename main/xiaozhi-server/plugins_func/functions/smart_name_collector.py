"""
智能姓名收集器
自动识别用户输入中的姓名信息并收集
"""

import re
import json
from typing import Dict, Any, Optional
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.providers.user.user_info_manager import UserInfoManager
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

# 智能姓名识别函数描述
smart_name_collector_function_desc = {
    "type": "function",
    "function": {
        "name": "smart_name_collector",
        "description": "智能识别用户输入中的姓名信息，如果检测到姓名则自动收集并保存",
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

# 姓名模式匹配规则
NAME_PATTERNS = [
    # 直接介绍姓名
    r'我叫(.+?)(?:，|。|！|？|$)',  # 我叫张三
    r'我的名字是(.+?)(?:，|。|！|？|$)',  # 我的名字是张三
    r'我是(.+?)(?:，|。|！|？|$)',  # 我是张三
    r'你可以叫我(.+?)(?:，|。|！|？|$)',  # 你可以叫我张三
    r'大家都叫我(.+?)(?:，|。|！|？|$)',  # 大家都叫我张三
    
    # 回答姓名问题
    r'^(.{2,10})$',  # 直接回答的短文本（2-10个字符）
    
    # 包含姓名的句子
    r'(.{2,4})是我的名字',  # 张三是我的名字
    r'(.{2,4})就是我的名字',  # 张三就是我的名字
]

# 中文姓名常见字符
CHINESE_NAME_CHARS = r'[\u4e00-\u9fff]'
ENGLISH_NAME_CHARS = r'[a-zA-Z]'

# 过滤词（不是姓名的词）
FILTER_WORDS = {
    '你好', '谢谢', '再见', '好的', '可以', '不行', '不知道', '没关系', 
    '朋友', '同学', '老师', '先生', '女士', '小姐', '帅哥', '美女',
    '小智', '小爱', '小度', '天猫精灵', '小艺', '小冰'
}


@register_function("smart_name_collector", smart_name_collector_function_desc, ToolType.SYSTEM_CTL)
def smart_name_collector(conn, user_input: str):
    """智能识别并收集用户姓名"""
    try:
        device_id = conn.device_id
        if not device_id:
            logger.bind(tag=TAG).error("设备ID为空，无法收集姓名")
            return ActionResponse(Action.ERROR, "设备ID为空", "无法收集姓名")
        
        if not user_input or not user_input.strip():
            return ActionResponse(Action.NONE, "输入为空", None)
        
        # 初始化用户信息管理器
        user_manager = UserInfoManager(conn.config)
        
        # 检查用户是否已有姓名
        has_name = user_manager.has_user_name(device_id)
        if has_name:
            # 用户已有姓名，不需要收集
            return ActionResponse(Action.NONE, "用户已有姓名", None)
        
        # 尝试从输入中提取姓名
        extracted_name = extract_name_from_input(user_input)
        
        if extracted_name:
            # 验证姓名是否有效
            if is_valid_name(extracted_name):
                # 保存姓名
                success = user_manager.update_user_name(device_id, extracted_name)
                
                if success:
                    welcome_message = f"很高兴认识你，{extracted_name}！我已经记住了你的名字。"
                    logger.bind(tag=TAG).info(f"智能收集到用户 {device_id} 的姓名: {extracted_name}")
                    
                    # 记录交互
                    user_manager.record_interaction(device_id, "smart_name_collection", user_input, welcome_message)
                    
                    return ActionResponse(Action.RESPONSE, welcome_message, welcome_message)
                else:
                    logger.bind(tag=TAG).error(f"保存用户 {device_id} 姓名失败")
                    return ActionResponse(Action.ERROR, "保存姓名失败", "抱歉，保存你的姓名时出现了问题")
            else:
                logger.bind(tag=TAG).debug(f"提取到的文本不是有效姓名: {extracted_name}")
                return ActionResponse(Action.NONE, "不是有效姓名", None)
        else:
            # 没有检测到姓名，可能需要进一步询问
            logger.bind(tag=TAG).debug(f"未从输入中检测到姓名: {user_input}")
            return ActionResponse(Action.NONE, "未检测到姓名", None)
            
    except Exception as e:
        logger.bind(tag=TAG).error(f"智能姓名收集失败: {e}")
        return ActionResponse(Action.ERROR, str(e), "姓名收集时出现错误")


def extract_name_from_input(text: str) -> Optional[str]:
    """从用户输入中提取可能的姓名"""
    if not text:
        return None
    
    text = text.strip()
    
    # 尝试各种模式匹配
    for pattern in NAME_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                name = match.strip()
                if name and is_valid_name(name):
                    return name
    
    # 如果没有匹配到模式，检查是否是简单的回答
    if len(text) <= 10 and is_valid_name(text):
        return text
    
    return None


def is_valid_name(name: str) -> bool:
    """验证是否是有效的姓名"""
    if not name or not name.strip():
        return False
    
    name = name.strip()
    
    # 长度检查
    if len(name) < 2 or len(name) > 20:
        return False
    
    # 过滤明显的非姓名词汇
    if name in FILTER_WORDS:
        return False
    
    # 检查是否包含姓名常见字符
    has_chinese = bool(re.search(CHINESE_NAME_CHARS, name))
    has_english = bool(re.search(ENGLISH_NAME_CHARS, name))
    
    if not (has_chinese or has_english):
        return False
    
    # 检查是否包含明显的非姓名字符
    invalid_chars = r'[0-9\s\.,;:!?@#$%^&*()_+=\[\]{}|\\:";\'<>?/~`]'
    if re.search(invalid_chars, name):
        return False
    
    # 检查是否全是重复字符
    if len(set(name)) == 1:
        return False
    
    return True


def should_ask_for_name(conn) -> bool:
    """判断是否应该询问用户姓名"""
    try:
        device_id = conn.device_id
        if not device_id:
            return False
        
        user_manager = UserInfoManager(conn.config)
        has_name = user_manager.has_user_name(device_id)
        
        return not has_name
    except Exception as e:
        logger.bind(tag=TAG).error(f"检查是否应该询问姓名失败: {e}")
        return False


def get_name_collection_prompt() -> str:
    """获取姓名收集的提示语"""
    prompts = [
        "你好！我是小智，很高兴认识你！请问你叫什么名字呢？",
        "欢迎使用小智！为了能更好地为你服务，请告诉我你的名字吧！",
        "你好！我是你的AI助手小智，请问怎么称呼你呢？",
        "很高兴见到你！请告诉我你的名字，这样我就能更好地记住你了！"
    ]
    
    import random
    return random.choice(prompts)

