"""
场景管理器
负责管理学习场景和步骤
"""

import json
from typing import Dict, List, Optional
from config.config_loader import load_config
from config.manage_api_client import (
    get_scenario_list, get_scenario_by_id, create_scenario, update_scenario, delete_scenario,
    get_scenario_steps, get_step_by_id, create_step, update_step, delete_step, reorder_scenario_steps
)


class ScenarioManager:
    """场景管理器"""
    
    def __init__(self):
        self.config = load_config()
    
    def get_active_scenarios(self, agent_id: str = None) -> List[Dict]:
        """获取活跃的场景列表"""
        try:
            print(f"=== get_active_scenarios 调试 ===")
            print(f"代理ID: {agent_id}")
            print(f"正在获取活跃场景列表")
            
            result = get_scenario_list(agent_id=agent_id, page=1, limit=100, is_active=True)
            # print(f"API调用结果: {result}")
            
            if result:
                scenarios = result.get("list", [])
                # print(f"原始场景列表: {scenarios}")
                active_scenarios = [s for s in scenarios if s.get("isActive", False)]
                # print(f"活跃场景列表: {active_scenarios}")
                # print(f"获取到 {len(scenarios)} 个场景，其中 {len(active_scenarios)} 个活跃场景")
                
                # for i, scenario in enumerate(active_scenarios):
                #     print(f"活跃场景 {i+1}:")
                #     print(f"  - 场景ID: {scenario.get('id', 'N/A')}")
                #     print(f"  - 场景名称: {scenario.get('scenarioName', 'N/A')}")
                #     print(f"  - 是否活跃: {scenario.get('isActive', 'N/A')}")
                #     print(f"  - 代理ID: {scenario.get('agentId', 'N/A')}")
                
                return active_scenarios
            else:
                print("获取活跃场景列表失败，API返回None")
                return []
                
        except Exception as e:
            print(f"获取活跃场景列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """获取场景信息"""
        try:
            print(f"=== scenario_manager.get_scenario 调试 ===")
            print(f"场景ID: {scenario_id}")
            
            result = get_scenario_by_id(scenario_id)
            # print(f"API调用结果: {result}")
            
            # if result:
            #     print(f"场景详情:")
            #     print(f"  - 场景ID: {result.get('id', 'N/A')}")
            #     print(f"  - 场景名称: {result.get('scenarioName', 'N/A')}")
            #     print(f"  - 是否活跃: {result.get('isActive', 'N/A')}")
            #     print(f"  - 代理ID: {result.get('agentId', 'N/A')}")
            # else:
            #     print("场景获取失败，返回None")
            
            return result
        except Exception as e:
            print(f"获取场景失败: {e}")
            traceback.print_exc()
            return None
    
    def create_scenario(self, scenario_data: Dict) -> Optional[str]:
        """创建场景"""
        try:
            result = create_scenario(scenario_data)
            if result:
                return result.get("id")
            return None
        except Exception as e:
            print(f"创建场景失败: {e}")
            return None
    
    def update_scenario(self, scenario_id: str, scenario_data: Dict) -> bool:
        """更新场景"""
        try:
            result = update_scenario(scenario_id, scenario_data)
            return result is not None
        except Exception as e:
            print(f"更新场景失败: {e}")
            return False
    
    def delete_scenario(self, scenario_id: str) -> bool:
        """删除场景"""
        try:
            result = delete_scenario(scenario_id)
            return result is not None
        except Exception as e:
            print(f"删除场景失败: {e}")
            return False
    
    def list_scenarios(self, agent_id: str = None, page: int = 1, size: int = 10) -> Optional[List[Dict]]:
        """获取场景列表"""
        try:
            result = get_scenario_list(agent_id=agent_id, page=page, limit=size)
            if result:
                return result.get("list", [])
            return None
        except Exception as e:
            print(f"获取场景列表失败: {e}")
            return None


class StepManager:
    """步骤管理器"""
    
    def __init__(self):
        self.config = load_config()
    
    def get_scenario_steps(self, scenario_id: str) -> List[Dict]:
        """获取场景的所有步骤"""
        try:
            result = get_scenario_steps(scenario_id)
            if result:
                steps = result if isinstance(result, list) else []
                # 按stepOrder字段排序
                steps.sort(key=lambda x: x.get('stepOrder', 0))
                return steps
            return []
        except Exception as e:
            print(f"获取场景步骤失败: {e}")
            return []
    
    def get_step(self, step_id: str) -> Optional[Dict]:
        """获取步骤信息"""
        try:
            return get_step_by_id(step_id)
        except Exception as e:
            print(f"获取步骤失败: {e}")
            return None
    
    def create_step(self, step_data: Dict) -> Optional[str]:
        """创建步骤"""
        try:
            result = create_step(step_data)
            if result:
                return result.get("id")
            return None
        except Exception as e:
            print(f"创建步骤失败: {e}")
            return None
    
    def update_step(self, step_id: str, step_data: Dict) -> bool:
        """更新步骤"""
        try:
            result = update_step(step_id, step_data)
            return result is not None
        except Exception as e:
            print(f"更新步骤失败: {e}")
            return False
    
    def delete_step(self, step_id: str) -> bool:
        """删除步骤"""
        try:
            result = delete_step(step_id)
            return result is not None
        except Exception as e:
            print(f"删除步骤失败: {e}")
            return False
    
    def reorder_steps(self, scenario_id: str, step_orders: List[Dict]) -> bool:
        """重新排序步骤"""
        try:
            result = reorder_scenario_steps(scenario_id, step_orders)
            return result is not None
        except Exception as e:
            print(f"重新排序步骤失败: {e}")
            return False


# 创建全局实例
scenario_manager = ScenarioManager()
step_manager = StepManager()

# 导入并创建 scenario_trigger 实例
from core.scenario.dialogue_executor import scenario_trigger 