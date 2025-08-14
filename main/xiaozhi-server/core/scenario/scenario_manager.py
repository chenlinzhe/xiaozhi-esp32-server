"""
场景管理器
负责管理学习场景和步骤
"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Optional
from config.config_loader import load_config


class ScenarioManager:
    """场景管理器"""
    
    def __init__(self):
        self.config = load_config()
        self.api_base_url = self.config.get("manager_api_url", "http://localhost:8002")
    
    async def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """获取场景信息"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/{scenario_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data")
                    else:
                        print(f"获取场景失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"获取场景失败: {e}")
            return None
    
    async def create_scenario(self, scenario_data: Dict) -> Optional[str]:
        """创建场景"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario"
                async with session.post(url, json=scenario_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {}).get("id")
                    else:
                        print(f"创建场景失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"创建场景失败: {e}")
            return None
    
    async def update_scenario(self, scenario_id: str, scenario_data: Dict) -> bool:
        """更新场景"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/{scenario_id}"
                async with session.put(url, json=scenario_data) as response:
                    return response.status == 200
        except Exception as e:
            print(f"更新场景失败: {e}")
            return False
    
    async def delete_scenario(self, scenario_id: str) -> bool:
        """删除场景"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/{scenario_id}"
                async with session.delete(url) as response:
                    return response.status == 200
        except Exception as e:
            print(f"删除场景失败: {e}")
            return False
    
    async def list_scenarios(self, agent_id: str = None, page: int = 1, size: int = 10) -> Optional[List[Dict]]:
        """获取场景列表"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario"
                params = {"page": page, "size": size}
                if agent_id:
                    params["agentId"] = agent_id
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {}).get("records", [])
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
        self.api_base_url = self.config.get("manager_api_url", "http://localhost:8002")
    
    async def get_scenario_steps(self, scenario_id: str) -> List[Dict]:
        """获取场景的所有步骤"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/{scenario_id}/steps"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        steps = data.get("data", [])
                        # 按order字段排序
                        steps.sort(key=lambda x: x.get('order', 0))
                        return steps
                    else:
                        print(f"获取场景步骤失败，状态码: {response.status}")
                        return []
        except Exception as e:
            print(f"获取场景步骤失败: {e}")
            return []
    
    async def get_step(self, step_id: str) -> Optional[Dict]:
        """获取步骤信息"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/step/{step_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data")
                    else:
                        print(f"获取步骤失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"获取步骤失败: {e}")
            return None
    
    async def create_step(self, step_data: Dict) -> Optional[str]:
        """创建步骤"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/step"
                async with session.post(url, json=step_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {}).get("id")
                    else:
                        print(f"创建步骤失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"创建步骤失败: {e}")
            return None
    
    async def update_step(self, step_id: str, step_data: Dict) -> bool:
        """更新步骤"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/step/{step_id}"
                async with session.put(url, json=step_data) as response:
                    return response.status == 200
        except Exception as e:
            print(f"更新步骤失败: {e}")
            return False
    
    async def delete_step(self, step_id: str) -> bool:
        """删除步骤"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/step/{step_id}"
                async with session.delete(url) as response:
                    return response.status == 200
        except Exception as e:
            print(f"删除步骤失败: {e}")
            return False
    
    async def reorder_steps(self, scenario_id: str, step_orders: List[Dict]) -> bool:
        """重新排序步骤"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/{scenario_id}/steps/reorder"
                async with session.put(url, json={"stepOrders": step_orders}) as response:
                    return response.status == 200
        except Exception as e:
            print(f"重新排序步骤失败: {e}")
            return False


# 创建全局实例
scenario_manager = ScenarioManager()
step_manager = StepManager()

# 导入并创建 scenario_trigger 实例
from core.scenario.dialogue_executor import scenario_trigger 