"""
对话步骤执行器
负责执行场景对话的各个步骤
"""

import json
import asyncio
from typing import Dict, List, Optional, Tuple
from .scenario_manager import scenario_manager, step_manager
from .learning_record_manager import learning_record_manager, LearningSession


class DialogueStepExecutor:
    """对话步骤执行器"""
    
    def __init__(self, scenario_id: str, child_name: str = None):
        self.scenario_id = scenario_id
        self.child_name = child_name or "小朋友"
        self.steps = []
        self.current_step_index = 0
        self.attempts = 0
        self.is_completed = False
        self.start_time = None
        self.completed_steps = 0
        self.total_steps = 0
        
        # 学习会话管理
        self.learning_session = LearningSession(learning_record_manager)
        
    async def initialize(self):
        """初始化执行器"""
        try:
            # 获取场景信息
            self.scenario = scenario_manager.get_scenario(self.scenario_id)
            if not self.scenario:
                raise Exception(f"场景不存在: {self.scenario_id}")
            
            # 获取步骤列表
            self.steps = step_manager.get_scenario_steps(self.scenario_id)
            self.total_steps = len(self.steps)
            
            # 重置状态
            self.current_step_index = 0
            self.attempts = 0
            self.is_completed = False
            self.start_time = asyncio.get_event_loop().time()
            
            # 开始学习会话
            self.learning_session.start_session(
                self.scenario_id,
                self.scenario.get('agentId', ''),
                self.child_name,
                self.total_steps
            )
            
            return True
        except Exception as e:
            print(f"初始化执行器失败: {e}")
            return False
    
    def get_current_step(self) -> Optional[Dict]:
        """获取当前步骤"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def execute_current_step(self, user_response: str) -> Dict:
        """执行当前对话步骤"""
        if self.is_completed:
            return {"type": "complete", "message": "对话已完成"}
        
        if self.current_step_index >= len(self.steps):
            self.is_completed = True
            return {"type": "complete", "message": "恭喜你完成了这个场景！"}
        
        current_step = self.get_current_step()
        if not current_step:
            return {"type": "error", "message": "步骤不存在"}
        
        # 替换儿童姓名
        ai_message = current_step.get('aiMessage', '').replace("**{childName}**", self.child_name)
        
        # 判断用户回答
        is_correct = self.judge_response(user_response, current_step)
        
        if is_correct:
            return self.handle_success(current_step)
        else:
            return self.handle_failure(current_step)
    
    def judge_response(self, user_response: str, step: Dict) -> bool:
        """判断用户回答是否正确"""
        try:
            expected_keywords = json.loads(step.get('expectedKeywords', '[]'))
            expected_phrases = json.loads(step.get('expectedPhrases', '[]'))
            success_condition = step.get('successCondition', 'partial')
            
            if success_condition == "exact":
                return user_response in expected_phrases
            elif success_condition == "partial":
                return any(phrase in user_response for phrase in expected_phrases)
            elif success_condition == "keyword":
                return any(keyword in user_response for keyword in expected_keywords)
            
            return False
        except Exception as e:
            print(f"判断回答失败: {e}")
            return False
    
    def handle_success(self, step: Dict) -> Dict:
        """处理成功情况"""
        self.current_step_index += 1
        self.attempts = 0
        self.completed_steps += 1
        
        # 记录步骤完成
        self.learning_session.complete_step()
        
        if self.current_step_index >= len(self.steps):
            self.is_completed = True
            return {"type": "complete", "message": "恭喜你完成了这个场景！"}
        else:
            next_step = self.get_current_step()
            ai_message = next_step.get('aiMessage', '').replace("**{childName}**", self.child_name)
            return {
                "type": "next", 
                "message": ai_message,
                "step_index": self.current_step_index,
                "total_steps": self.total_steps
            }
    
    def handle_failure(self, step: Dict) -> Dict:
        """处理失败情况 - 不再使用替代消息和AI消息"""
        self.attempts += 1
        max_attempts = step.get('maxAttempts', 3)
        
        if self.attempts >= max_attempts:
            # 超过最大尝试次数，结束当前步骤
            return {
                "type": "timeout",
                "message": "让我们继续下一步",
                "attempts": self.attempts,
                "max_attempts": max_attempts
            }
        else:
            # 重试当前步骤
            return {
                "type": "retry",
                "message": "让我们再试一次",
                "attempts": self.attempts,
                "max_attempts": max_attempts
            }
    
    def get_progress(self) -> Dict:
        """获取进度信息"""
        return {
            "current_step": self.current_step_index + 1,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "progress_percentage": (self.completed_steps / self.total_steps * 100) if self.total_steps > 0 else 0,
            "is_completed": self.is_completed
        }
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.start_time:
            return {}
        
        duration = asyncio.get_event_loop().time() - self.start_time
        success_rate = (self.completed_steps / self.total_steps * 100) if self.total_steps > 0 else 0
        
        return {
            "duration": int(duration),
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "success_rate": round(success_rate, 2),
            "is_completed": self.is_completed
        }
    
    async def end_session(self) -> Optional[str]:
        """结束学习会话并保存记录"""
        if self.learning_session.start_time:
            # 设置难度评分（基于尝试次数和成功率）
            avg_attempts = self.attempts / max(self.completed_steps, 1)
            if avg_attempts <= 1.5:
                difficulty_rating = 1
            elif avg_attempts <= 2.5:
                difficulty_rating = 2
            elif avg_attempts <= 3.5:
                difficulty_rating = 3
            else:
                difficulty_rating = 4
            
            self.learning_session.set_difficulty_rating(difficulty_rating)
            
            # 添加学习笔记
            progress = self.get_progress()
            note = f"完成进度: {progress['progress_percentage']:.1f}%, 总尝试次数: {self.attempts}"
            self.learning_session.add_note(note)
            
            # 保存学习记录
            return await self.learning_session.end_session()
        
        return None


class ScenarioTrigger:
    """场景触发器"""
    
    def __init__(self):
        self.scenario_manager = scenario_manager
    
    def detect_trigger(self, user_input: str, input_type: str = "voice") -> Optional[Dict]:
        """检测场景触发"""
        if input_type == "voice":
            return self.detect_voice_trigger(user_input)
        elif input_type == "visual":
            return self.detect_visual_trigger(user_input)
        elif input_type == "button":
            return self.detect_button_trigger(user_input)
        return None
    
    def detect_voice_trigger(self, text: str) -> Optional[Dict]:
        """语音触发检测"""
        try:
            scenarios = self.scenario_manager.get_active_scenarios()
            for scenario in scenarios:
                trigger_keywords = json.loads(scenario.get('triggerKeywords', '[]'))
                if any(keyword in text for keyword in trigger_keywords):
                    return scenario
            return None
        except Exception as e:
            print(f"语音触发检测失败: {e}")
            return None
    
    def detect_visual_trigger(self, card_id: str) -> Optional[Dict]:
        """视觉触发检测"""
        try:
            scenarios = self.scenario_manager.get_active_scenarios()
            for scenario in scenarios:
                trigger_cards = json.loads(scenario.get('triggerCards', '[]'))
                if card_id in trigger_cards:
                    return scenario
            return None
        except Exception as e:
            print(f"视觉触发检测失败: {e}")
            return None
    
    def detect_button_trigger(self, button_id: str) -> Optional[Dict]:
        """按钮触发检测"""
        try:
            scenarios = self.scenario_manager.get_active_scenarios()
            for scenario in scenarios:
                if scenario.get('triggerType') == 'button' and scenario.get('scenarioCode') == button_id:
                    return scenario
            return None
        except Exception as e:
            print(f"按钮触发检测失败: {e}")
            return None


# 全局实例
scenario_trigger = ScenarioTrigger()
