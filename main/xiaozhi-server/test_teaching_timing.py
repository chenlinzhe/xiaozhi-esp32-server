#!/usr/bin/env python3
"""
测试教学模式计时功能
验证在说完第一句话后才开始计时
"""

import time
import asyncio
from core.scenario.chat_status_manager import ChatStatusManager
from core.scenario.teaching_handler import TeachingHandler
from core.utils.redis_client import get_redis_client

class MockConnection:
    """模拟连接对象"""
    def __init__(self):
        self.device_id = "test_device_001"
        self.session_id = "test_session_001"
        self.dialogue = []
        self.tts = None
        self.loop = asyncio.get_event_loop()
    
    def put(self, message):
        self.dialogue.append(message)

def test_teaching_timing():
    """测试教学模式计时功能"""
    print("=== 测试教学模式计时功能 ===")
    
    # 初始化组件
    chat_status_manager = ChatStatusManager()
    mock_connection = MockConnection()
    teaching_handler = TeachingHandler(mock_connection)
    
    user_id = "test_user_001"
    child_name = "小明"
    
    print(f"用户ID: {user_id}")
    print(f"儿童姓名: {child_name}")
    
    # 测试1: 检查初始会话数据
    print("\n--- 测试1: 检查初始会话数据 ---")
    session_data = chat_status_manager.redis_client.get_session_data(f"teaching_{user_id}")
    print(f"初始会话数据: {session_data}")
    
    # 测试2: 模拟开始教学模式
    print("\n--- 测试2: 模拟开始教学模式 ---")
    try:
        # 异步调用开始教学会话
        future = asyncio.run_coroutine_threadsafe(
            chat_status_manager._start_teaching_session(user_id, child_name, from_mode_switch=True),
            mock_connection.loop
        )
        result = future.result(timeout=10)
        print(f"开始教学会话结果: {result}")
        
        if result and result.get("success"):
            # 检查会话数据
            session_data = chat_status_manager.redis_client.get_session_data(f"teaching_{user_id}")
            print(f"教学会话数据: {session_data}")
            print(f"等待开始时间: {session_data.get('wait_start_time')}")
            
            # 验证等待开始时间应该为None
            if session_data.get("wait_start_time") is None:
                print("✓ 等待开始时间正确设置为None")
            else:
                print("✗ 等待开始时间应该为None")
                
    except Exception as e:
        print(f"开始教学会话失败: {e}")
    
    # 测试3: 模拟TTS消息发送完成
    print("\n--- 测试3: 模拟TTS消息发送完成 ---")
    try:
        # 更新等待开始时间
        chat_status_manager.update_wait_start_time(user_id)
        
        # 检查更新后的会话数据
        session_data = chat_status_manager.redis_client.get_session_data(f"teaching_{user_id}")
        print(f"更新后的会话数据: {session_data}")
        print(f"等待开始时间: {session_data.get('wait_start_time')}")
        
        # 验证等待开始时间应该不为None
        if session_data.get("wait_start_time") is not None:
            print("✓ 等待开始时间正确更新")
        else:
            print("✗ 等待开始时间应该已更新")
            
    except Exception as e:
        print(f"更新等待开始时间失败: {e}")
    
    # 测试4: 测试超时检查
    print("\n--- 测试4: 测试超时检查 ---")
    try:
        # 等待1秒后检查超时
        time.sleep(1)
        
        future = asyncio.run_coroutine_threadsafe(
            chat_status_manager.check_teaching_timeout(user_id),
            mock_connection.loop
        )
        result = future.result(timeout=5)
        print(f"超时检查结果: {result}")
        
        if result is None:
            print("✓ 超时检查正确返回None（未超时）")
        else:
            print(f"超时检查返回: {result}")
            
    except Exception as e:
        print(f"超时检查失败: {e}")
    
    # 清理测试数据
    print("\n--- 清理测试数据 ---")
    try:
        chat_status_manager.redis_client.delete_session_data(f"teaching_{user_id}")
        print("✓ 测试数据清理完成")
    except Exception as e:
        print(f"清理测试数据失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_teaching_timing()
