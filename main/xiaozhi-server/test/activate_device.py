#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小智设备激活脚本
用于激活测试设备，以便进行完整的聊天功能测试
"""

import requests
import json
import sys
import time
from typing import Optional

def activate_device(device_mac: str, activation_code: str, manager_api_url: str = "http://127.0.0.1:8002", username: str = "ningwenjie", password: str = "310113Nm.") -> bool:
    """
    激活设备
    
    Args:
        device_mac: 设备MAC地址
        activation_code: 激活码
        manager_api_url: 管理API地址
    
    Returns:
        bool: 激活是否成功
    """
    try:
        print(f"正在激活设备 {device_mac}，激活码: {activation_code}")
        
        # 先登录获取token
        login_data = {
            "username": username,
            "password": password,
            "captcha": "test"
        }
        
        login_response = requests.post(
            f"{manager_api_url}/xiaozhi/user/login",
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"登录失败: HTTP {login_response.status_code}")
            return False
            
        login_result = login_response.json()
        print(f"登录响应: {json.dumps(login_result, indent=2, ensure_ascii=False)}")
        
        # 检查不同的响应格式
        if login_result.get('code') == 200:
            # 标准格式
            pass
        elif login_result.get('success') == True:
            # 成功格式
            pass
        elif 'data' in login_result:
            # 有数据格式
            pass
        else:
            print(f"登录失败: {login_result}")
            return False
            
        # 获取token
        token = None
        for token_field in ['accessToken', 'token', 'access_token']:
            if token_field in login_result.get('data', {}):
                token = login_result['data'][token_field]
                break
                
        if not token:
            print("登录成功但未获取到token")
            return False
            
        print(f"登录成功，获取到token")
        
        # 构建激活请求
        activation_data = {
            "deviceMac": device_mac,
            "activationCode": activation_code
        }
        
        # 手动添加设备
        device_data = {
            "agentId": "test_agent",
            "board": "xiaozhi-python-test",
            "appVersion": "1.0.0",
            "macAddress": device_mac
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.post(
            f"{manager_api_url}/xiaozhi/device/manual-add",
            json=device_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"设备添加成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"设备添加失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"激活异常: {str(e)}")
        return False

def get_activation_code(device_mac: str, ota_url: str = "http://127.0.0.1:8002/xiaozhi/ota/") -> Optional[str]:
    """
    获取设备激活码
    
    Args:
        device_mac: 设备MAC地址
        ota_url: OTA服务器地址
    
    Returns:
        str: 激活码，如果获取失败返回None
    """
    try:
        print(f"正在获取设备 {device_mac} 的激活码...")
        
        # 构建OTA请求数据
        ota_data = {
            "version": 0,
            "uuid": "",
            "application": {
                "name": "xiaozhi-python-test",
                "version": "1.0.0",
                "compile_time": "2025-01-17 10:00:00",
                "idf_version": "4.4.3",
                "elf_sha256": "1234567890abcdef1234567890abcdef1234567890abcdef"
            },
            "ota": {
                "label": "xiaozhi-python-test",
            },
            "board": {
                "type": "xiaozhi-python-test",
                "ssid": "xiaozhi-python-test",
                "rssi": 0,
                "channel": 0,
                "ip": "192.168.1.1",
                "mac": device_mac
            },
            "flash_size": 0,
            "minimum_free_heap_size": 0,
            "mac_address": device_mac,
            "chip_model_name": "",
            "chip_info": {
                "model": 0,
                "cores": 0,
                "revision": 0,
                "features": 0
            },
            "partition_table": [
                {
                    "label": "",
                    "type": 0,
                    "subtype": 0,
                    "address": 0,
                    "size": 0
                }
            ]
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Device-Id': device_mac,
            'Client-Id': 'python_test_client'
        }
        
        response = requests.post(ota_url, json=ota_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            ota_result = response.json()
            print(f"OTA响应: {json.dumps(ota_result, indent=2, ensure_ascii=False)}")
            
            if ota_result.get('activation') and ota_result['activation'].get('code'):
                activation_code = ota_result['activation']['code']
                print(f"获取到激活码: {activation_code}")
                return activation_code
            else:
                print("OTA响应中没有激活码")
                return None
        else:
            print(f"OTA请求失败: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"获取激活码异常: {str(e)}")
        return None

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='小智设备激活工具')
    parser.add_argument('--device-mac', '-m', required=True, help='设备MAC地址')
    parser.add_argument('--activation-code', '-c', help='激活码（如果不提供，将自动获取）')
    parser.add_argument('--manager-api', '-a', default='http://127.0.0.1:8002', help='管理API地址')
    parser.add_argument('--ota-url', '-o', default='http://127.0.0.1:8002/xiaozhi/ota/', help='OTA服务器地址')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("小智设备激活工具")
    print("=" * 60)
    print(f"设备MAC: {args.device_mac}")
    print(f"管理API: {args.manager_api}")
    print(f"OTA地址: {args.ota_url}")
    print()
    
    # 获取或使用激活码
    activation_code = args.activation_code
    if not activation_code:
        activation_code = get_activation_code(args.device_mac, args.ota_url)
        if not activation_code:
            print("❌ 无法获取激活码")
            return 1
    
    # 激活设备
    if activate_device(args.device_mac, activation_code, args.manager_api):
        print("✅ 设备激活成功！")
        print("现在可以运行完整的聊天功能测试了")
        return 0
    else:
        print("❌ 设备激活失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
