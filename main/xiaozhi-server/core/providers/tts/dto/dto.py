from enum import Enum
from typing import Union, Optional
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class SentenceType(Enum):
    # 说话阶段
    FIRST = "FIRST"  # 首句话
    MIDDLE = "MIDDLE"  # 说话中
    LAST = "LAST"  # 最后一句


class ContentType(Enum):
    # 内容类型
    TEXT = "TEXT"  # 文本内容
    FILE = "FILE"  # 文件内容
    ACTION = "ACTION"  # 动作内容


class InterfaceType(Enum):
    # 接口类型
    DUAL_STREAM = "DUAL_STREAM"  # 双流式
    SINGLE_STREAM = "SINGLE_STREAM"  # 单流式
    NON_STREAM = "NON_STREAM"  # 非流式


class TTSMessageDTO:
    def __init__(
        self,
        sentence_id: str,
        # 说话阶段
        sentence_type: SentenceType,
        # 内容类型
        content_type: ContentType,
        # 内容详情，一般是需要转换的文本或者音频的歌词
        content_detail: Optional[str] = None,
        # 如果内容类型为文件，则需要传入文件路径
        content_file: Optional[str] = None,
        # 语速配置（0.2-3.0倍速，1.0为正常语速）
        speech_rate: Optional[float] = None,
    ):
        self.sentence_id = sentence_id
        self.sentence_type = sentence_type
        self.content_type = content_type
        self.content_detail = content_detail
        self.content_file = content_file
        self.speech_rate = speech_rate
        
        # 添加详细的日志记录
        logger.bind(tag=TAG).info(f"=== TTSMessageDTO创建 ===")
        logger.bind(tag=TAG).info(f"sentence_id: {sentence_id}")
        logger.bind(tag=TAG).info(f"sentence_type: {sentence_type.name}")
        logger.bind(tag=TAG).info(f"content_type: {content_type.name}")
        logger.bind(tag=TAG).info(f"content_detail: {content_detail}")
        logger.bind(tag=TAG).info(f"content_file: {content_file}")
        logger.bind(tag=TAG).info(f"speech_rate: {speech_rate}")
