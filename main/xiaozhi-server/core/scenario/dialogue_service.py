"""
场景对话服务
"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
from config.config_loader import load_config


class DialogueService:
    """对话服务"""
    
    def __init__(self):
        self.config = load_config()
        self.api_base_url = self.config.get("manager_api_url", "http://localhost:8002")
        self.sessions = {}
    
    async def start_scenario(self, session_id: str, scenario_id: str, child_name: str) -> Dict:
        """开始场景对话"""
        try:
            # 获取场景信息
            scenario = await self._get_scenario(scenario_id)
            if not scenario:
                return {"success": False, "error": "场景不存在"}
            
            # 获取场景步骤
            steps = await self._get_scenario_steps(scenario_id)
            if not steps:
                return {"success": False, "error": "场景步骤不存在"}
            
            # 创建会话
            self.sessions[session_id] = {
                "scenario_id": scenario_id,
                "child_name": child_name,
                "scenario": scenario,
                "steps": steps,
                "current_step": 0,
                "start_time": datetime.now(),
                "evaluations": []
            }
            
            # 返回第一个步骤
            first_step = steps[0] if steps else {}
            return {
                "success": True,
                "session_id": session_id,
                "scenario_name": scenario.get("scenarioName", ""),
                "current_step": first_step,
                "total_steps": len(steps)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def process_response(self, session_id: str, user_text: str) -> Dict:
        """处理用户回复"""
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": "会话不存在"}
        
        # 评估回复
        evaluation = self._evaluate_response(session, user_text)
        session["evaluations"].append(evaluation)
        
        # 判断是否进入下一步
        if evaluation["score"] >= 60 or evaluation["retry_count"] >= 3:
            # 进入下一步
            session["current_step"] += 1
            if session["current_step"] >= len(session["steps"]):
                # 场景完成
                await self._complete_scenario(session)
                return {
                    "success": True,
                    "action": "completed",
                    "evaluation": evaluation,
                    "final_score": self._calculate_final_score(session)
                }
            else:
                # 下一步
                next_step = session["steps"][session["current_step"]]
                return {
                    "success": True,
                    "action": "next_step",
                    "current_step": next_step,
                    "evaluation": evaluation
                }
        else:
            # 重试当前步骤
            current_step = session["steps"][session["current_step"]]
            return {
                "success": True,
                "action": "retry",
                "current_step": current_step,
                "evaluation": evaluation
            }
    
    def _evaluate_response(self, session: Dict, user_text: str) -> Dict:
        """评估用户回复"""
        current_step = session["steps"][session["current_step"]]
        expected_keywords = current_step.get("expectedKeywords", "").split(",") if current_step.get("expectedKeywords") else []
        
        # 简单关键词匹配
        matches = 0
        for keyword in expected_keywords:
            if keyword.strip().lower() in user_text.lower():
                matches += 1
        
        total = len(expected_keywords) if expected_keywords else 1
        score = int((matches / total) * 100)
        
        # 计算重试次数
        retry_count = 0
        for eval in session["evaluations"]:
            if eval["step_index"] == session["current_step"]:
                retry_count += 1
        
        return {
            "score": score,
            "feedback": "太棒了！" if score >= 80 else "不错！" if score >= 60 else "加油！",
            "step_index": session["current_step"],
            "retry_count": retry_count
        }
    
    def _calculate_final_score(self, session: Dict) -> int:
        """计算最终分数"""
        if not session["evaluations"]:
            return 0
        
        total = sum(eval["score"] for eval in session["evaluations"])
        return int(total / len(session["evaluations"]))
    
    async def _get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """获取场景信息"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/{scenario_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data")
                    return None
        except Exception as e:
            print(f"获取场景失败: {e}")
            return None
    
    async def _get_scenario_steps(self, scenario_id: str) -> List[Dict]:
        """获取场景步骤"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/{scenario_id}/steps"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    return []
        except Exception as e:
            print(f"获取场景步骤失败: {e}")
            return []
    
    async def _complete_scenario(self, session: Dict):
        """完成场景"""
        try:
            final_score = self._calculate_final_score(session)
            
            # 保存学习记录
            record_data = {
                "scenario_id": session["scenario_id"],
                "child_name": session["child_name"],
                "success_rate": final_score,
                "learning_duration": (datetime.now() - session["start_time"]).total_seconds(),
                "created_at": datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session_client:
                url = f"{self.api_base_url}/xiaozhi/learning-record"
                await session_client.post(url, json=record_data)
                
        except Exception as e:
            print(f"完成场景失败: {e}")
    
    async def get_scenarios(self) -> List[Dict]:
        """获取场景列表"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/scenario/list"
                params = {"page": 1, "limit": 100}
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        scenarios = data.get("data", {}).get("list", [])
                        return [s for s in scenarios if s.get("isActive", False)]
                    return []
        except Exception as e:
            print(f"获取场景列表失败: {e}")
            return []
