#!/usr/bin/env python3
"""
更新API Token脚本
"""

import os
import yaml
import requests
from datetime import datetime


def read_config(config_path):
    """读取配置文件"""
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def write_config(config_path, config):
    """写入配置文件"""
    with open(config_path, "w", encoding="utf-8") as file:
        yaml.dump(config, file, default_flow_style=False, allow_unicode=True)


def get_new_token():
    """获取新的token"""
    print("=== 获取新的API Token ===")
    
    # 获取manager-api地址
    config_path = "data/.config.yaml"
    if not os.path.exists(config_path):
        print(f"配置文件不存在: {config_path}")
        return None
    
    config = read_config(config_path)
    api_url = config.get("manager-api", {}).get("url", "")
    
    if not api_url:
        print("未配置manager-api地址")
        return None
    
    # 构建登录URL
    base_url = api_url.replace("/xiaozhi", "")
    login_url = f"{base_url}/xiaozhi/auth/login"
    
    print(f"Manager API地址: {base_url}")
    print(f"登录URL: {login_url}")
    
    # 获取用户输入
    username = input("请输入用户名: ")
    password = input("请输入密码: ")
    
    try:
        # 发送登录请求
        login_data = {
            "username": username,
            "password": password
        }
        
        print("正在登录...")
        response = requests.post(login_url, json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                token = data.get("data", {}).get("token")
                if token:
                    print(f"登录成功！获取到新token: {token}")
                    return token
                else:
                    print("登录成功但未获取到token")
            else:
                print(f"登录失败: {data.get('msg', '未知错误')}")
        else:
            print(f"登录请求失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"登录请求异常: {e}")
    
    return None


def update_config_token(new_token):
    """更新配置文件中的token"""
    config_path = "data/.config.yaml"
    
    if not os.path.exists(config_path):
        print(f"配置文件不存在: {config_path}")
        return False
    
    try:
        config = read_config(config_path)
        
        # 备份原配置
        backup_path = f"data/.config.yaml.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        write_config(backup_path, config)
        print(f"原配置已备份到: {backup_path}")
        
        # 更新token
        if "manager-api" not in config:
            config["manager-api"] = {}
        
        config["manager-api"]["secret"] = new_token
        
        # 写入新配置
        write_config(config_path, config)
        print(f"Token已更新到配置文件: {config_path}")
        return True
        
    except Exception as e:
        print(f"更新配置文件失败: {e}")
        return False


def main():
    """主函数"""
    print("=== API Token更新工具 ===")
    print("此工具将帮助您获取新的API token并更新配置文件")
    print()
    
    # 获取新token
    new_token = get_new_token()
    if not new_token:
        print("获取新token失败")
        return
    
    # 确认更新
    print()
    confirm = input("是否更新配置文件中的token? (y/N): ")
    if confirm.lower() != 'y':
        print("取消更新")
        return
    
    # 更新配置
    if update_config_token(new_token):
        print("Token更新成功！")
        print("请重启xiaozhi-server以使新token生效")
    else:
        print("Token更新失败")


if __name__ == "__main__":
    main()
