"""
基于思维导图的系统配置文件
"""

from typing import Dict, List, Any
from enum import Enum


class SystemMode(Enum):
    """系统模式枚举"""
    FREE_CHAT = "free_chat"
    TEACHING_MODE = "teaching_mode"


class UserState(Enum):
    """用户状态枚举"""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    RESPONDING = "responding"
    LEARNING = "learning"


class MindMapConfig:
    """思维导图系统配置"""
    
    # 系统入口配置
    SYSTEM_ENTRY = {
        "asr_enabled": True,
        "text_processing_enabled": True,
        "mode_detection_enabled": True
    }
    
    # 模式判断配置
    MODE_DETECTION = {
        "teaching_mode_keywords": [
            "教学模式", "教学", "学习模式", "学习", "开始教学", 
            "我要学习", "教我", "学习时间", "上课", "开始学习",
            "我想学习", "教我学习", "学习一下", "开始上课"
        ],
        "free_mode_keywords": [
            "自由模式", "自由聊天", "聊天模式", "聊天", "结束教学",
            "不学了", "休息", "玩一会", "随便聊", "停止学习",
            "不想学了", "休息一下", "聊聊天", "玩一下"
        ],
        "confidence_threshold": 0.7
    }
    
    # 状态管理配置
    STATE_MANAGEMENT = {
        "redis_enabled": True,
        "session_timeout": 3600,  # 1小时
        "state_persistence": True,
        "auto_cleanup": True
    }
    
    # 教学场景配置
    TEACHING_SCENARIO = {
        "immediate_start": True,      # 立即开始教学
        "timeout_handling": True,     # 超时处理
        "smart_evaluation": True,     # 智能评估
        "adaptive_feedback": True,    # 自适应反馈
        "progress_tracking": True     # 进度跟踪
    }
    
    # 超时机制配置
    TIMEOUT_CONFIG = {
        "base_timeout": 20,           # 基础超时时间
        "min_timeout": 10,            # 最小超时时间
        "max_timeout": 60,            # 最大超时时间
        "difficulty_factor": 2,       # 难度因子
        "age_factor": 3,              # 年龄因子
        "retry_factor": 5             # 重试因子
    }
    
    # 智能评估配置
    ASSESSMENT_CONFIG = {
        "excellent_threshold": 90,    # 优秀阈值
        "good_threshold": 80,         # 良好阈值
        "pass_threshold": 60,         # 及格阈值
        "max_retries": 3,             # 最大重试次数
        "fuzzy_matching": True,       # 模糊匹配
        "semantic_similarity": True,  # 语义相似度
        "confidence_scoring": True    # 置信度评分
    }
    
    # 反馈系统配置
    FEEDBACK_CONFIG = {
        "praise_messages": [
            "太棒了！你说得很好！",
            "真聪明！回答得非常好！",
            "哇！你真是太厉害了！",
            "完美！你学得很快！",
            "真棒！你的理解很准确！",
            "太厉害了！回答得很完整！"
        ],
        "encouragement_messages": [
            "没关系，我们再试一次！",
            "加油，你可以的！",
            "别着急，慢慢来~",
            "再想想看，我相信你！",
            "不要灰心，再试一次！",
            "你已经很接近了，再努力一下！"
        ],
        "suggestion_messages": [
            "可以尝试更完整的表达",
            "注意关键词的使用",
            "可以多说一些细节",
            "回答得很好，可以再详细一些",
            "尝试用更自然的表达方式"
        ]
    }
    
    # 流程控制配置
    FLOW_CONTROL = {
        "auto_progression": True,     # 自动推进
        "smart_retry": True,          # 智能重试
        "skip_on_failure": True,      # 失败时跳过
        "completion_tracking": True   # 完成度跟踪
    }
    
    # 性能优化配置
    PERFORMANCE_CONFIG = {
        "caching_enabled": True,      # 启用缓存
        "async_processing": True,     # 异步处理
        "connection_pooling": True,   # 连接池
        "error_recovery": True        # 错误恢复
    }
    
    @classmethod
    def get_mode_keywords(cls, mode: SystemMode) -> List[str]:
        """获取指定模式的关键词"""
        if mode == SystemMode.TEACHING_MODE:
            return cls.MODE_DETECTION["teaching_mode_keywords"]
        elif mode == SystemMode.FREE_CHAT:
            return cls.MODE_DETECTION["free_mode_keywords"]
        return []
    
    @classmethod
    def get_timeout(cls, difficulty: int = 1, age: int = 6, retries: int = 0) -> int:
        """计算动态超时时间"""
        base_timeout = cls.TIMEOUT_CONFIG["base_timeout"]
        difficulty_factor = difficulty * cls.TIMEOUT_CONFIG["difficulty_factor"]
        age_factor = max(0, (6 - age) * cls.TIMEOUT_CONFIG["age_factor"])
        retry_factor = retries * cls.TIMEOUT_CONFIG["retry_factor"]
        
        total_timeout = base_timeout + difficulty_factor + age_factor + retry_factor
        
        min_timeout = cls.TIMEOUT_CONFIG["min_timeout"]
        max_timeout = cls.TIMEOUT_CONFIG["max_timeout"]
        
        return max(min_timeout, min(max_timeout, total_timeout))
    
    @classmethod
    def get_feedback_message(cls, score: int, retry_count: int = 0) -> str:
        """获取反馈消息"""
        import random
        
        if score >= cls.ASSESSMENT_CONFIG["excellent_threshold"]:
            return random.choice(cls.FEEDBACK_CONFIG["praise_messages"])
        elif score >= cls.ASSESSMENT_CONFIG["good_threshold"]:
            return random.choice(cls.FEEDBACK_CONFIG["praise_messages"])
        elif score >= cls.ASSESSMENT_CONFIG["pass_threshold"]:
            return random.choice(cls.FEEDBACK_CONFIG["encouragement_messages"])
        else:
            if retry_count > 0:
                return random.choice(cls.FEEDBACK_CONFIG["encouragement_messages"])
            else:
                return random.choice(cls.FEEDBACK_CONFIG["suggestion_messages"])
    
    @classmethod
    def is_teaching_mode_command(cls, text: str) -> bool:
        """判断是否为教学模式命令"""
        keywords = cls.get_mode_keywords(SystemMode.TEACHING_MODE)
        return any(keyword in text for keyword in keywords)
    
    @classmethod
    def is_free_mode_command(cls, text: str) -> bool:
        """判断是否为自由模式命令"""
        keywords = cls.get_mode_keywords(SystemMode.FREE_CHAT)
        return any(keyword in text for keyword in keywords)
