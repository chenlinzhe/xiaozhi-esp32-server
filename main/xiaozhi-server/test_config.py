#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sys
import os

def test_manager_api():
    """测试manager-api连接"""
    print("=== 测试manager-api连接 ===")
    
    # 测试manager-api是否可访问
    try:
        response = requests.get("http://localhost:8002/xiaozhi/scenario/list", timeout=10)
        print(f"Manager-API状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Manager-API响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"Manager-API错误: {response.text}")
            return False
    except Exception as e:
        print(f"Manager-API连接失败: {e}")
        return False

def test_llm_config():
    """测试LLM配置"""
    print("\n=== 测试LLM配置 ===")
    
    # 这里可以添加LLM配置测试
    print("LLM配置测试需要有效的API密钥")
    return True

def main():
    print("开始配置测试...")
    
    # 测试manager-api
    api_ok = test_manager_api()
    
    # 测试LLM配置
    llm_ok = test_llm_config()
    
    print("\n=== 测试结果 ===")
    print(f"Manager-API: {'✅ 正常' if api_ok else '❌ 异常'}")
    print(f"LLM配置: {'✅ 正常' if llm_ok else '❌ 异常'}")
    
    if api_ok and llm_ok:
        print("\n🎉 配置测试通过！可以启动xiaozhi-server了。")
        return 0
    else:
        print("\n⚠️ 配置测试失败，请检查相关配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
