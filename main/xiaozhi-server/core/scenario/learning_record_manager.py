"""
学习记录管理器
负责记录和管理儿童的学习数据
"""

import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Optional
from config.config_loader import get_config_from_api


class LearningRecordManager:
    """学习记录管理器"""
    
    def __init__(self):
        self.config = get_config_from_api()
        self.api_base_url = self.config.get("manager_api_url", "http://localhost:8002")
    
    async def create_learning_record(self, record_data: Dict) -> Optional[str]:
        """创建学习记录"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/learning-record"
                async with session.post(url, json=record_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {}).get("id")
                    else:
                        print(f"创建学习记录失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"创建学习记录失败: {e}")
            return None
    
    async def update_learning_record(self, record_id: str, record_data: Dict) -> bool:
        """更新学习记录"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/learning-record/{record_id}"
                async with session.put(url, json=record_data) as response:
                    return response.status == 200
        except Exception as e:
            print(f"更新学习记录失败: {e}")
            return False
    
    async def get_learning_statistics(self, agent_id: str, child_name: str) -> Optional[Dict]:
        """获取学习统计信息"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/xiaozhi/learning-record/statistics"
                params = {"agentId": agent_id, "childName": child_name}
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data")
                    else:
                        print(f"获取学习统计失败，状态码: {response.status}")
                        return None
        except Exception as e:
            print(f"获取学习统计失败: {e}")
            return None
    
    def calculate_success_rate(self, completed_steps: int, total_steps: int) -> float:
        """计算成功率"""
        if total_steps == 0:
            return 0.0
        return round((completed_steps / total_steps) * 100, 2)
    
    def calculate_duration(self, start_time: datetime, end_time: datetime) -> int:
        """计算学习时长（秒）"""
        if not start_time or not end_time:
            return 0
        duration = (end_time - start_time).total_seconds()
        return int(duration)
    
    def format_duration(self, seconds: int) -> str:
        """格式化时长显示"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}分{remaining_seconds}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分"


class LearningSession:
    """学习会话管理器"""
    
    def __init__(self, record_manager: LearningRecordManager):
        self.record_manager = record_manager
        self.current_record_id = None
        self.start_time = None
        self.end_time = None
        self.scenario_id = None
        self.agent_id = None
        self.child_name = None
        self.total_steps = 0
        self.completed_steps = 0
        self.difficulty_rating = None
        self.notes = ""
    
    def start_session(self, scenario_id: str, agent_id: str, child_name: str, total_steps: int):
        """开始学习会话"""
        self.scenario_id = scenario_id
        self.agent_id = agent_id
        self.child_name = child_name
        self.total_steps = total_steps
        self.start_time = datetime.now()
        self.completed_steps = 0
        self.difficulty_rating = None
        self.notes = ""
    
    def complete_step(self):
        """完成一个步骤"""
        self.completed_steps += 1
    
    def set_difficulty_rating(self, rating: int):
        """设置难度评分"""
        self.difficulty_rating = rating
    
    def add_note(self, note: str):
        """添加学习笔记"""
        if self.notes:
            self.notes += "\n" + note
        else:
            self.notes = note
    
    async def end_session(self) -> Optional[str]:
        """结束学习会话并保存记录"""
        if not self.start_time:
            return None
        
        self.end_time = datetime.now()
        
        # 计算统计数据
        duration = self.record_manager.calculate_duration(self.start_time, self.end_time)
        success_rate = self.record_manager.calculate_success_rate(self.completed_steps, self.total_steps)
        
        # 构建记录数据
        record_data = {
            "agentId": self.agent_id,
            "scenarioId": self.scenario_id,
            "childName": self.child_name,
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat(),
            "totalSteps": self.total_steps,
            "completedSteps": self.completed_steps,
            "successRate": success_rate,
            "learningDuration": duration,
            "difficultyRating": self.difficulty_rating,
            "notes": self.notes
        }
        
        # 保存记录
        record_id = await self.record_manager.create_learning_record(record_data)
        
        # 重置会话状态
        self.reset_session()
        
        return record_id
    
    def reset_session(self):
        """重置会话状态"""
        self.current_record_id = None
        self.start_time = None
        self.end_time = None
        self.scenario_id = None
        self.agent_id = None
        self.child_name = None
        self.total_steps = 0
        self.completed_steps = 0
        self.difficulty_rating = None
        self.notes = ""


# 全局实例
learning_record_manager = LearningRecordManager()
