#!/usr/bin/env python3
"""
测试场景教学处理器
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.scenario.teaching_handler import TeachingHandler
from config.logger import setup_logging

def test_teaching_handler():
    """测试TeachingHandler的基本功能"""
    logger = setup_logging()
    logger.info("开始测试TeachingHandler")
    
    # 创建一个模拟的connection对象
    class MockConnection:
        def __init__(self):
            self.device_id = "test_device_001"
            self.session_id = "test_session_001"
            self.tts = None
            self.sentence_id = None
            self.dialogue = None
            self.loop = None
            
        def put(self, message):
            logger.info(f"模拟对话记录: {message}")
    
    # 创建模拟connection
    mock_connection = MockConnection()
    
    # 创建TeachingHandler实例
    teaching_handler = TeachingHandler(mock_connection)
    
    # 测试设置儿童姓名
    teaching_handler.set_child_name("小明")
    logger.info(f"儿童姓名设置为: {teaching_handler.child_name}")
    
    # 测试处理聊天模式（由于没有真实的TTS和对话系统，这里只是验证不会出错）
    try:
        result = teaching_handler.handle_chat_mode("你好")
        logger.info(f"处理聊天模式结果: {result}")
    except Exception as e:
        logger.error(f"处理聊天模式时出错: {e}")
    
    logger.info("TeachingHandler测试完成")

if __name__ == "__main__":
    test_teaching_handler()
