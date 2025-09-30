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
    """智能识别并收集用户姓名 - 已禁用，改为连接时处理"""
    # 用户信息检查已移至WebSocket连接时处理，此函数不再执行问名字逻辑
    logger.bind(tag=TAG).info("smart_name_collector函数已禁用，用户信息检查已移至连接时处理")
    return ActionResponse(Action.NONE, "用户信息检查已移至连接时处理", None)


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

