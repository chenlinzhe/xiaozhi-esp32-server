#!/usr/bin/env python3
"""
聊天模式集成测试脚本
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.scenario.chat_status_manager import ChatStatusManager
from core.scenario.dialogue_service import DialogueService
from core.utils.redis_client import get_redis_client


async def test_chat_mode_integration():
    """测试聊天模式集成功能"""
    print("=== 聊天模式集成测试 ===")
    
    # 初始化组件
    chat_manager = ChatStatusManager()
    dialogue_service = DialogueService()
    redis_client = get_redis_client()
    
    # 测试用户ID
    test_user_id = "test_device_001"
    child_name = "小明"
    
    print(f"\n1. 测试模式切换命令识别")
    test_commands = [
        "切换到教学模式",
        "教学模式",
        "开始教学",
        "切换到自由模式", 
        "自由模式",
        "自由聊天",
        "你好，今天天气怎么样？"  # 普通对话
    ]
    
    for cmd in test_commands:
        mode = chat_manager.is_mode_switch_command(cmd)
        print(f"   '{cmd}' -> {mode}")
    
    print(f"\n2. 测试聊天状态存储")
    # 设置教学模式
    success = chat_manager.set_user_chat_status(test_user_id, "teaching_mode")
    print(f"   设置教学模式: {success}")
    
    # 获取状态
    status = chat_manager.get_user_chat_status(test_user_id)
    print(f"   当前状态: {status}")
    
    # 设置自由模式
    success = chat_manager.set_user_chat_status(test_user_id, "free_mode")
    print(f"   设置自由模式: {success}")
    
    status = chat_manager.get_user_chat_status(test_user_id)
    print(f"   当前状态: {status}")
    
    print(f"\n3. 测试用户输入处理")
    test_inputs = [
        "切换到教学模式",
        "你好，我想学习",
        "切换到自由模式",
        "今天天气怎么样？"
    ]
    
    for user_input in test_inputs:
        print(f"\n   处理输入: '{user_input}'")
        try:
            result = await chat_manager.handle_user_input(test_user_id, user_input, child_name)
            if result and result.get("success"):
                action = result.get("action")
                ai_message = result.get("ai_message", "")
                print(f"   结果: {action} - {ai_message}")
            else:
                print(f"   结果: 失败 - {result.get('error', '未知错误')}")
        except Exception as e:
            print(f"   异常: {e}")
    
    print(f"\n4. 测试超时检查")
    try:
        timeout_result = await chat_manager.check_teaching_timeout(test_user_id)
        if timeout_result:
            print(f"   超时结果: {timeout_result}")
        else:
            print(f"   无超时")
    except Exception as e:
        print(f"   超时检查异常: {e}")
    
    print(f"\n5. 清理测试数据")
    # 清理Redis中的测试数据
    redis_client.delete_chat_status(test_user_id)
    redis_client.delete_session_data(f"teaching_{test_user_id}")
    print(f"   清理完成")
    
    print(f"\n=== 测试完成 ===")


async def test_dialogue_service():
    """测试对话服务"""
    print("\n=== 对话服务测试 ===")
    
    dialogue_service = DialogueService()
    
    print("1. 获取场景列表")
    try:
        scenarios = await dialogue_service.get_scenarios()
        print(f"   获取到 {len(scenarios)} 个场景")
        for i, scenario in enumerate(scenarios[:3]):  # 只显示前3个
            print(f"   {i+1}. {scenario.get('scenarioName', 'Unknown')} - {scenario.get('scenarioType', 'Unknown')}")
    except Exception as e:
        print(f"   获取场景列表失败: {e}")
    
    print("\n2. 获取默认教学场景")
    try:
        default_scenario = await dialogue_service.get_default_teaching_scenario()
        if default_scenario:
            print(f"   默认场景: {default_scenario.get('scenarioName', 'Unknown')}")
        else:
            print("   没有默认教学场景")
    except Exception as e:
        print(f"   获取默认场景失败: {e}")


if __name__ == "__main__":
    try:
        # 运行测试
        asyncio.run(test_chat_mode_integration())
        asyncio.run(test_dialogue_service())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
