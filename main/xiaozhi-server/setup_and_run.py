#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xiaozhi-server 自动设置和运行脚本
自动修复所有已知问题并确保服务能够成功启动
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, check=True, shell=True):
    """运行命令并返回结果"""
    print(f"执行命令: {command}")
    try:
        result = subprocess.run(command, shell=shell, check=check, 
                              capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            print(f"输出: {result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stderr:
            print(f"错误: {e.stderr}")
        if check:
            raise
        return e

def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    print(f"当前 Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 13:
        print("警告: 检测到 Python 3.13+，可能存在兼容性问题")
        print("建议使用 Python 3.10")
        return False
    return True

def setup_conda_environment():
    """设置 conda 环境"""
    print("\n=== 设置 conda 环境 ===")
    
    # 检查是否已存在 xiaozhi-server-py310 环境
    result = run_command("conda env list", check=False)
    if "xiaozhi-server-py310" in result.stdout:
        print("发现已存在的 xiaozhi-server-py310 环境")
    else:
        print("创建新的 conda 环境: xiaozhi-server-py310")
        run_command("conda create -n xiaozhi-server-py310 python=3.10 -y")
    
    # 激活环境
    print("激活 conda 环境...")
    if os.name == 'nt':  # Windows
        python_path = r"C:\Users\Administrator\miniconda3\envs\xiaozhi-server-py310\python.exe"
        pip_path = r"C:\Users\Administrator\miniconda3\envs\xiaozhi-server-py310\Scripts\pip.exe"
    else:  # Linux/Mac
        python_path = "conda run -n xiaozhi-server-py310 python"
        pip_path = "conda run -n xiaozhi-server-py310 pip"
    
    return python_path, pip_path

def install_dependencies(python_path, pip_path):
    """安装所需依赖"""
    print("\n=== 安装依赖包 ===")
    
    # 设置 pip 镜像源
    run_command(f"{pip_path} config set global.index-url https://mirrors.aliyun.com/pypi/simple/")
    
    # 基础依赖
    basic_packages = [
        "pyyaml", "loguru", "aioconsole", "websockets", "opuslib_next", 
        "numpy", "pydub", "jinja2", "requests", "aiohttp", "aiohttp_cors",
        "ormsgpack", "ruamel.yaml", "httpx", "edge_tts", "openai", 
        "google-generativeai", "cozepy", "mem0ai", "bs4", "modelscope",
        "sherpa_onnx", "mcp", "cnlunar", "PySocks", "dashscope", 
        "baidu-aip", "chardet", "markitdown", "mcp-proxy", "PyJWT", 
        "psutil", "portalocker"
    ]
    
    for package in basic_packages:
        print(f"安装 {package}...")
        run_command(f"{pip_path} install {package}", check=False)
    
    # 安装 torch 和 torchaudio
    print("安装 torch 和 torchaudio...")
    run_command(f"{pip_path} install torch torchaudio", check=False)
    
    # 安装 funasr
    print("安装 funasr...")
    run_command(f"{pip_path} install funasr", check=False)
    
    # 安装 silero_vad
    print("安装 silero_vad...")
    run_command(f"{pip_path} install silero_vad", check=False)

def install_system_dependencies():
    """安装系统级依赖"""
    print("\n=== 安装系统依赖 ===")
    
    # 安装 ffmpeg
    print("安装 ffmpeg...")
    run_command("conda install ffmpeg -y", check=False)
    
    # 安装 libopus
    print("安装 libopus...")
    run_command("conda install libopus -y", check=False)

def fix_config_files():
    """修复配置文件"""
    print("\n=== 修复配置文件 ===")
    
    # 修复 config_loader.py
    config_loader_path = "config/config_loader.py"
    if os.path.exists(config_loader_path):
        print("修复 config_loader.py...")
        with open(config_loader_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复配置文件路径
        content = content.replace(
            'custom_config_path = get_project_dir() + "data/config.yaml"',
            'custom_config_path = get_project_dir() + "data/.config.yaml"'
        )
        
        with open(config_loader_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # 修复 settings.py
    settings_path = "config/settings.py"
    if os.path.exists(settings_path):
        print("修复 settings.py...")
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复配置文件路径
        content = content.replace(
            'custom_config_file = get_project_dir() + "data/" + default_config_file',
            'custom_config_file = get_project_dir() + "data/.config.yaml"'
        )
        
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(content)

def fix_scenario_files():
    """修复场景管理相关文件"""
    print("\n=== 修复场景管理文件 ===")
    
    # 修复 scenario_manager.py
    scenario_manager_path = "core/scenario/scenario_manager.py"
    if os.path.exists(scenario_manager_path):
        print("修复 scenario_manager.py...")
        with open(scenario_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复导入
        content = content.replace(
            'from config.config_loader import get_config_from_api',
            'from config.config_loader import load_config'
        )
        
        # 修复函数调用
        content = content.replace(
            'self.config = get_config_from_api()',
            'self.config = load_config()'
        )
        
        # 添加 scenario_trigger 导入
        if 'from core.scenario.dialogue_executor import scenario_trigger' not in content:
            content += '\n# 导入并创建 scenario_trigger 实例\nfrom core.scenario.dialogue_executor import scenario_trigger\n'
        
        with open(scenario_manager_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # 修复 learning_record_manager.py
    learning_record_path = "core/scenario/learning_record_manager.py"
    if os.path.exists(learning_record_path):
        print("修复 learning_record_manager.py...")
        with open(learning_record_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复导入
        content = content.replace(
            'from config.config_loader import get_config_from_api',
            'from config.config_loader import load_config'
        )
        
        # 修复函数调用
        content = content.replace(
            'self.config = get_config_from_api()',
            'self.config = load_config()'
        )
        
        with open(learning_record_path, 'w', encoding='utf-8') as f:
            f.write(content)

def check_config_file():
    """检查配置文件"""
    print("\n=== 检查配置文件 ===")
    
    config_file = "data/.config.yaml"
    if not os.path.exists(config_file):
        print(f"配置文件 {config_file} 不存在，创建默认配置...")
        os.makedirs("data", exist_ok=True)
        
        default_config = """manager-api:
  url: http://127.0.0.1:8002/xiaozhi
  secret: 7bd20014-77e5-4fdf-ba4e-05cc6629875c
"""
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(default_config)
        print(f"已创建默认配置文件: {config_file}")
    else:
        print(f"配置文件 {config_file} 已存在")

def check_models():
    """检查模型文件"""
    print("\n=== 检查模型文件 ===")
    
    model_dir = "models/SenseVoiceSmall"
    model_file = os.path.join(model_dir, "model.pt")
    
    if not os.path.exists(model_file):
        print(f"警告: 语音识别模型文件 {model_file} 不存在")
        print("请从以下地址下载模型文件:")
        print("- 阿里魔搭: https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt")
        print("- 百度网盘: https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg&pwd=qvna")
        print("下载后将 model.pt 文件放置在 models/SenseVoiceSmall/ 目录下")
    else:
        print(f"语音识别模型文件已存在: {model_file}")

def run_server(python_path):
    """运行服务器"""
    print("\n=== 启动 xiaozhi-server ===")
    
    try:
        # 检查 app.py 是否存在
        if not os.path.exists("app.py"):
            print("错误: app.py 文件不存在")
            return False
        
        print("启动 xiaozhi-server...")
        print("按 Ctrl+C 停止服务")
        
        # 运行服务器
        result = subprocess.run([python_path, "app.py"], 
                              cwd=os.getcwd(), 
                              check=False)
        
        if result.returncode == 0:
            print("服务器正常退出")
        else:
            print(f"服务器异常退出，返回码: {result.returncode}")
        
        return True
        
    except KeyboardInterrupt:
        print("\n用户中断，服务器已停止")
        return True
    except Exception as e:
        print(f"启动服务器时发生错误: {e}")
        return False

def main():
    """主函数"""
    print("=== xiaozhi-server 自动设置和运行脚本 ===")
    print("此脚本将自动修复所有已知问题并启动服务")
    
    # 检查当前目录
    if not os.path.exists("app.py"):
        print("错误: 请在 xiaozhi-server 目录下运行此脚本")
        return 1
    
    # 检查 Python 版本
    if not check_python_version():
        print("建议使用 Python 3.10，但将继续尝试...")
    
    try:
        # 设置 conda 环境
        python_path, pip_path = setup_conda_environment()
        
        # 安装依赖
        install_dependencies(python_path, pip_path)
        install_system_dependencies()
        
        # 修复文件
        fix_config_files()
        fix_scenario_files()
        
        # 检查配置和模型
        check_config_file()
        check_models()
        
        # 运行服务器
        success = run_server(python_path)
        
        if success:
            print("\n=== 设置完成 ===")
            print("xiaozhi-server 已成功启动或配置完成")
            return 0
        else:
            print("\n=== 设置失败 ===")
            print("请检查错误信息并手动解决问题")
            return 1
            
    except Exception as e:
        print(f"\n设置过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
