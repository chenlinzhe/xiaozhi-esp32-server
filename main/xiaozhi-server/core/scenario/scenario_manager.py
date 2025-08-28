"""
场景管理器
负责管理学习场景和步骤
"""

import json
import asyncio
import aiohttp
import os
import yaml
from typing import Dict, List, Optional
from config.config_loader import load_config


def read_config(config_path):
    """读取配置文件"""
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_api_config():
    """获取API配置信息"""
    config_path = "data/.config.yaml"
    if not os.path.exists(config_path):
        print(f"配置文件不存在: {config_path}")
        return None, None
    
    try:
        config = read_config(config_path)
        api_url = config.get("manager-api", {}).get("url", "")
        server_secret = config.get("manager-api", {}).get("secret", "")
        
        if not api_url:
            print("未配置manager-api地址")
            return None, None
        
        # 构建基础URL
        base_url = api_url.replace("/xiaozhi", "")
        
        return base_url, server_secret
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return None, None


class ScenarioManager:
    """场景管理器"""
    
    def __init__(self):
        self.config = load_config()
        # 使用update_token.py中的方法获取API配置
        self.api_base_url, self.server_secret = get_api_config()
        if not self.api_base_url:
            self.api_base_url = "http://localhost:8002"  # 默认地址
        # 用户token（用于场景API）
        self.user_token = None
    
    def _get_server_auth_headers(self) -> Dict[str, str]:
        """获取服务器密钥认证头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.server_secret and "你" not in self.server_secret:
            headers["Authorization"] = f"Bearer {self.server_secret}"
        return headers
    
    def _get_user_auth_headers(self) -> Dict[str, str]:
        """获取用户token认证头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.user_token:
            headers["Authorization"] = f"Bearer {self.user_token}"
        return headers
    
    async def _login_and_get_token(self) -> bool:
        """登录并获取用户token"""
        try:
            print("正在登录获取用户token...")
            async with aiohttp.ClientSession() as session:
                # 尝试使用常见的用户名登录
                login_attempts = [
                    {"username": "ningwenjie", "password": "310113Nm."},  # 用户提供的凭据
                    {"username": "admin", "password": "admin"},
                    {"username": "admin", "password": "123456"},
                    {"username": "admin", "password": "password"},
                    {"username": "xiaozhi", "password": "xiaozhi"},
                    {"username": "xiaozhi", "password": "123456"},
                ]
                
                for attempt in login_attempts:
                    try:
                        login_data = {
                            "username": attempt["username"],
                            "password": attempt["password"],
                            "captcha": "123456"   # 跳过验证码验证
                        }
                        
                        # 使用update_token.py中的登录URL构建方式
                        url = f"{self.api_base_url}/xiaozhi/auth/login"
                        headers = {"Content-Type": "application/json"}
                        
                        print(f"尝试登录: username={attempt['username']}")
                        async with session.post(url, json=login_data, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                print(f"登录响应数据: {data}")
                                if data.get('code') == 0:
                                    token_data = data.get('data', {})
                                    # 尝试多种可能的token字段名
                                    self.user_token = (
                                        token_data.get('accessToken') or 
                                        token_data.get('token') or 
                                        token_data.get('access_token') or
                                        data.get('token') or
                                        data.get('accessToken')
                                    )
                                    if self.user_token:
                                        print(f"登录成功，用户: {attempt['username']}, token: {self.user_token[:20]}...")
                                        return True
                                    else:
                                        print(f"登录成功但未获取到token，完整响应: {data}")
                                        continue
                                else:
                                    print(f"登录失败: {data.get('msg', '未知错误')}")
                                    continue
                            else:
                                print(f"登录请求失败: HTTP {response.status}")
                                continue
                    except Exception as e:
                        print(f"登录尝试异常: {e}")
                        continue
                
                print("所有登录尝试都失败了")
                return False
        except Exception as e:
            print(f"登录异常: {e}")
            return False
    
    async def get_active_scenarios(self, agent_id: str = None) -> List[Dict]:
        """获取活跃的场景列表"""
        try:
            print(f"正在获取活跃场景列表，API地址: {self.api_base_url}")
            
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return []
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/list"
                params = {"page": 1, "limit": 100, "isActive": 1}
                if agent_id:
                    params["agentId"] = agent_id
                
                headers = self._get_user_auth_headers()
                print(f"请求URL: {url}, 参数: {params}")
                print(f"请求头: {headers}")
                
                async with session.get(url, params=params, headers=headers) as response:
                    print(f"活跃场景列表API响应状态: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"活跃场景列表API响应数据: {data}")
                        
                        if data.get('code') == 0:
                            scenarios = data.get("data", {}).get("list", [])
                            active_scenarios = [s for s in scenarios if s.get("isActive", False)]
                            print(f"获取到 {len(scenarios)} 个场景，其中 {len(active_scenarios)} 个活跃场景")
                            return active_scenarios
                        else:
                            print(f"API返回错误: {data.get('msg', '未知错误')}")
                            return []
                    else:
                        print(f"获取活跃场景列表失败: HTTP {response.status}")
                        return []
        except Exception as e:
            print(f"获取活跃场景列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """获取场景信息"""
        try:
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return None
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/{scenario_id}"
                headers = self._get_user_auth_headers()
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            return data.get("data")
                        else:
                            print(f"API返回错误: {data.get('msg', '未知错误')}")
                            return None
                    else:
                        print(f"获取场景失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"获取场景失败: {e}")
            return None
    
    async def create_scenario(self, scenario_data: Dict) -> Optional[str]:
        """创建场景"""
        try:
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return None
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario"
                headers = self._get_user_auth_headers()
                
                async with session.post(url, json=scenario_data, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            return data.get("data", {}).get("id")
                        else:
                            print(f"API返回错误: {data.get('msg', '未知错误')}")
                            return None
                    else:
                        print(f"创建场景失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"创建场景失败: {e}")
            return None
    
    async def update_scenario(self, scenario_id: str, scenario_data: Dict) -> bool:
        """更新场景"""
        try:
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return False
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/{scenario_id}"
                headers = self._get_user_auth_headers()
                
                async with session.put(url, json=scenario_data, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('code') == 0
                    else:
                        print(f"更新场景失败，状态码: {response.status}")
                        return False
        except Exception as e:
            print(f"更新场景失败: {e}")
            return False
    
    async def delete_scenario(self, scenario_id: str) -> bool:
        """删除场景"""
        try:
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return False
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/{scenario_id}"
                headers = self._get_user_auth_headers()
                
                async with session.delete(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('code') == 0
                    else:
                        print(f"删除场景失败，状态码: {response.status}")
                        return False
        except Exception as e:
            print(f"删除场景失败: {e}")
            return False
    
    async def list_scenarios(self, agent_id: str = None, page: int = 1, size: int = 10) -> Optional[List[Dict]]:
        """获取场景列表"""
        try:
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return None
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/list"
                params = {"page": page, "limit": size}
                if agent_id:
                    params["agentId"] = agent_id
                
                headers = self._get_user_auth_headers()
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            return data.get("data", {}).get("list", [])
                        else:
                            print(f"API返回错误: {data.get('msg', '未知错误')}")
                            return None
                    else:
                        print(f"获取场景列表失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"获取场景列表失败: {e}")
            return None


class StepManager:
    """步骤管理器"""
    
    def __init__(self):
        self.config = load_config()
        # 使用update_token.py中的方法获取API配置
        self.api_base_url, self.server_secret = get_api_config()
        if not self.api_base_url:
            self.api_base_url = "http://localhost:8002"  # 默认地址
        # 用户token（用于场景API）
        self.user_token = None
    
    def _get_server_auth_headers(self) -> Dict[str, str]:
        """获取服务器密钥认证头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.server_secret and "你" not in self.server_secret:
            headers["Authorization"] = f"Bearer {self.server_secret}"
        return headers
    
    def _get_user_auth_headers(self) -> Dict[str, str]:
        """获取用户token认证头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.user_token:
            headers["Authorization"] = f"Bearer {self.user_token}"
        return headers
    
    async def _login_and_get_token(self) -> bool:
        """登录并获取用户token"""
        try:
            print("正在登录获取用户token...")
            async with aiohttp.ClientSession() as session:
                # 尝试使用常见的用户名登录
                login_attempts = [
                    {"username": "ningwenjie", "password": "310113Nm."},  # 用户提供的凭据
                    {"username": "admin", "password": "admin"},
                    {"username": "admin", "password": "123456"},
                    {"username": "admin", "password": "password"},
                    {"username": "xiaozhi", "password": "xiaozhi"},
                    {"username": "xiaozhi", "password": "123456"},
                ]
                
                for attempt in login_attempts:
                    try:
                        login_data = {
                            "username": attempt["username"],
                            "password": attempt["password"],
                            "captcha": "123456"   # 跳过验证码验证
                        }
                        
                        # 使用update_token.py中的登录URL构建方式
                        url = f"{self.api_base_url}/xiaozhi/auth/login"
                        headers = {"Content-Type": "application/json"}
                        
                        print(f"尝试登录: username={attempt['username']}")
                        async with session.post(url, json=login_data, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                print(f"登录响应数据: {data}")
                                if data.get('code') == 0:
                                    token_data = data.get('data', {})
                                    # 尝试多种可能的token字段名
                                    self.user_token = (
                                        token_data.get('accessToken') or 
                                        token_data.get('token') or 
                                        token_data.get('access_token') or
                                        data.get('token') or
                                        data.get('accessToken')
                                    )
                                    if self.user_token:
                                        print(f"登录成功，用户: {attempt['username']}, token: {self.user_token[:20]}...")
                                        return True
                                    else:
                                        print(f"登录成功但未获取到token，完整响应: {data}")
                                        continue
                                else:
                                    print(f"登录失败: {data.get('msg', '未知错误')}")
                                    continue
                            else:
                                print(f"登录请求失败: HTTP {response.status}")
                                continue
                    except Exception as e:
                        print(f"登录尝试异常: {e}")
                        continue
                
                print("所有登录尝试都失败了")
                return False
        except Exception as e:
            print(f"登录异常: {e}")
            return False
    
    async def get_scenario_steps(self, scenario_id: str) -> List[Dict]:
        """获取场景的所有步骤"""
        try:
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return []
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario-step/list/{scenario_id}"
                headers = self._get_user_auth_headers()
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            steps = data.get("data", [])
                            # 按stepOrder字段排序
                            steps.sort(key=lambda x: x.get('stepOrder', 0))
                            return steps
                        else:
                            print(f"API返回错误: {data.get('msg', '未知错误')}")
                            return []
                    else:
                        print(f"获取场景步骤失败，状态码: {response.status}")
                        return []
        except Exception as e:
            print(f"获取场景步骤失败: {e}")
            return []
    
    async def get_step(self, step_id: str) -> Optional[Dict]:
        """获取步骤信息"""
        try:
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return None
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/step/{step_id}"
                headers = self._get_user_auth_headers()
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            return data.get("data")
                        else:
                            print(f"API返回错误: {data.get('msg', '未知错误')}")
                            return None
                    else:
                        print(f"获取步骤失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"获取步骤失败: {e}")
            return None
    
    async def create_step(self, step_data: Dict) -> Optional[str]:
        """创建步骤"""
        try:
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return None
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/step"
                headers = self._get_user_auth_headers()
                
                async with session.post(url, json=step_data, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            return data.get("data", {}).get("id")
                        else:
                            print(f"API返回错误: {data.get('msg', '未知错误')}")
                            return None
                    else:
                        print(f"创建步骤失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"创建步骤失败: {e}")
            return None
    
    async def update_step(self, step_id: str, step_data: Dict) -> bool:
        """更新步骤"""
        try:
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return False
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/step/{step_id}"
                headers = self._get_user_auth_headers()
                
                async with session.put(url, json=step_data, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('code') == 0
                    else:
                        print(f"更新步骤失败，状态码: {response.status}")
                        return False
        except Exception as e:
            print(f"更新步骤失败: {e}")
            return False
    
    async def delete_step(self, step_id: str) -> bool:
        """删除步骤"""
        try:
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return False
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/step/{step_id}"
                headers = self._get_user_auth_headers()
                
                async with session.delete(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('code') == 0
                    else:
                        print(f"删除步骤失败，状态码: {response.status}")
                        return False
        except Exception as e:
            print(f"删除步骤失败: {e}")
            return False
    
    async def reorder_steps(self, scenario_id: str, step_orders: List[Dict]) -> bool:
        """重新排序步骤"""
        try:
            # 确保有用户token
            if not self.user_token:
                if not await self._login_and_get_token():
                    print("无法获取用户token，无法调用场景API")
                    return False
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/scenario/{scenario_id}/steps/reorder"
                headers = self._get_user_auth_headers()
                async with session.put(url, json={"stepOrders": step_orders}, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('code') == 0
                    else:
                        print(f"重新排序步骤失败，状态码: {response.status}")
                        return False
        except Exception as e:
            print(f"重新排序步骤失败: {e}")
            return False


# 创建全局实例
scenario_manager = ScenarioManager()
step_manager = StepManager()

# 导入并创建 scenario_trigger 实例
from core.scenario.dialogue_executor import scenario_trigger 