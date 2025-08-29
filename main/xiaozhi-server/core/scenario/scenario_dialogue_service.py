"""
场景对话服务
负责处理场景学习和对话流程
"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from config.config_loader import load_config
from core.scenario.scenario_manager import ScenarioManager, StepManager
from core.scenario.learning_record_manager import LearningRecordManager


class ScenarioDialogueService:
    """场景对话服务"""
    
    def __init__(self):
        self.config = load_config()
        # 使用配置文件中的manager-api.url，如果不存在则使用默认值
        manager_api_config = self.config.get("manager-api", {})
        self.api_base_url = manager_api_config.get("url", "http://localhost:8002")
        self.scenario_manager = ScenarioManager()
        self.step_manager = StepManager()
        self.learning_manager = LearningRecordManager()
        
        # 当前对话状态
        self.current_sessions = {}  # session_id -> DialogueSession
        
    async def start_scenario_dialogue(self, session_id: str, scenario_id: str, child_name: str) -> Dict:
        """开始场景对话"""
        try:
            # 获取场景信息
            scenario = self.scenario_manager.get_scenario(scenario_id)
            if not scenario:
                return {"success": False, "error": "场景不存在"}
            
            # 获取场景步骤
            steps = self.step_manager.get_scenario_steps(scenario_id)
            if not steps:
                return {"success": False, "error": "场景步骤不存在"}
            
            # 创建对话会话
            session = DialogueSession(
                session_id=session_id,
                scenario_id=scenario_id,
                child_name=child_name,
                scenario=scenario,
                steps=steps
            )
            
            self.current_sessions[session_id] = session
            
            # 获取第一个步骤
            first_step = session.get_current_step()
            if not first_step:
                return {"success": False, "error": "场景步骤配置错误"}
            
            # 返回开始信息
            return {
                "success": True,
                "session_id": session_id,
                "scenario_name": scenario.get("scenarioName", ""),
                "current_step": first_step,
                "total_steps": len(steps),
                "current_step_index": 0
            }
            
        except Exception as e:
            return {"success": False, "error": f"启动场景对话失败: {str(e)}"}
    
    async def process_user_response(self, session_id: str, user_text: str) -> Dict:
        """处理用户回复"""
        try:
            session = self.current_sessions.get(session_id)
            if not session:
                return {"success": False, "error": "对话会话不存在"}
            
            # 评估用户回复
            evaluation = await self._evaluate_response(session, user_text)
            
            # 更新会话状态
            session.update_with_response(user_text, evaluation)
            
            # 检查是否需要进入下一步
            if session.should_proceed_to_next():
                next_step = session.get_next_step()
                if next_step:
                    return {
                        "success": True,
                        "action": "next_step",
                        "current_step": next_step,
                        "current_step_index": session.current_step_index,
                        "total_steps": len(session.steps),
                        "evaluation": evaluation
                    }
                else:
                    # 场景完成
                    await self._complete_scenario(session)
                    return {
                        "success": True,
                        "action": "completed",
                        "evaluation": evaluation,
                        "final_score": session.get_final_score()
                    }
            else:
                # 需要重试当前步骤
                current_step = session.get_current_step()
                return {
                    "success": True,
                    "action": "retry",
                    "current_step": current_step,
                    "evaluation": evaluation,
                    "retry_count": session.get_current_retry_count()
                }
                
        except Exception as e:
            return {"success": False, "error": f"处理用户回复失败: {str(e)}"}
    
    async def _evaluate_response(self, session: 'DialogueSession', user_text: str) -> Dict:
        """评估用户回复"""
        current_step = session.get_current_step()
        if not current_step:
            return {"score": 0, "feedback": "步骤配置错误"}
        
        # 获取期望的关键词和短语
        expected_keywords = current_step.get("expectedKeywords", "").split(",") if current_step.get("expectedKeywords") else []
        expected_phrases = current_step.get("expectedPhrases", "").split(",") if current_step.get("expectedPhrases") else []
        
        # 简单的关键词匹配评估
        score = 0
        feedback = ""
        
        # 检查关键词匹配
        keyword_matches = 0
        for keyword in expected_keywords:
            if keyword.strip().lower() in user_text.lower():
                keyword_matches += 1
        
        # 检查短语匹配
        phrase_matches = 0
        for phrase in expected_phrases:
            if phrase.strip().lower() in user_text.lower():
                phrase_matches += 1
        
        # 计算分数
        total_keywords = len(expected_keywords) if expected_keywords else 1
        total_phrases = len(expected_phrases) if expected_phrases else 1
        
        keyword_score = (keyword_matches / total_keywords) * 50 if total_keywords > 0 else 0
        phrase_score = (phrase_matches / total_phrases) * 50 if total_phrases > 0 else 0
        
        score = keyword_score + phrase_score
        
        # 生成反馈
        if score >= 80:
            feedback = "太棒了！你说得很好！"
        elif score >= 60:
            feedback = "不错！再试试看。"
        elif score >= 40:
            feedback = "加油！你可以做得更好。"
        else:
            feedback = "没关系，我们再试一次。"
        
        return {
            "score": int(score),
            "feedback": feedback,
            "keyword_matches": keyword_matches,
            "phrase_matches": phrase_matches,
            "expected_keywords": expected_keywords,
            "expected_phrases": expected_phrases
        }
    
    async def _complete_scenario(self, session: 'DialogueSession'):
        """完成场景学习"""
        try:
            # 计算最终分数
            final_score = session.get_final_score()
            
            # 记录学习记录
            record_data = {
                "record_id": f"record_{session.session_id}_{int(datetime.now().timestamp())}",
                "agent_id": session.scenario.get("agentId", ""),
                "scenario_id": session.scenario_id,
                "child_name": session.child_name,
                "start_time": session.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_steps": len(session.steps),
                "completed_steps": session.completed_steps,
                "success_rate": final_score,
                "learning_duration": (datetime.now() - session.start_time).total_seconds(),
                "difficulty_rating": session.scenario.get("difficultyLevel", 1),
                "notes": f"场景学习完成，最终得分：{final_score}分",
                "created_at": datetime.now().isoformat()
            }
            
            await self.learning_manager.save_learning_record(record_data)
            
            # 清理会话
            if session.session_id in self.current_sessions:
                del self.current_sessions[session.session_id]
                
        except Exception as e:
            print(f"完成场景学习失败: {e}")
    
    async def get_available_scenarios(self, agent_id: str = None) -> List[Dict]:
        """获取可用的场景列表"""
        try:
            scenarios = self.scenario_manager.list_scenarios(agent_id=agent_id)
            if scenarios:
                # 只返回启用的场景
                return [s for s in scenarios if s.get("isActive", False)]
            return []
        except Exception as e:
            print(f"获取场景列表失败: {e}")
            return []
    
    async def get_session_status(self, session_id: str) -> Optional[Dict]:
        """获取会话状态"""
        session = self.current_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "scenario_name": session.scenario.get("scenarioName", ""),
            "current_step_index": session.current_step_index,
            "total_steps": len(session.steps),
            "completed_steps": session.completed_steps,
            "current_retry_count": session.get_current_retry_count(),
            "start_time": session.start_time.isoformat()
        }


class DialogueSession:
    """对话会话"""
    
    def __init__(self, session_id: str, scenario_id: str, child_name: str, scenario: Dict, steps: List[Dict]):
        self.session_id = session_id
        self.scenario_id = scenario_id
        self.child_name = child_name
        self.scenario = scenario
        self.steps = steps
        
        self.current_step_index = 0
        self.completed_steps = 0
        self.current_retry_count = 0
        self.max_retries = 3
        self.start_time = datetime.now()
        
        # 记录每个步骤的评估结果
        self.step_evaluations = []
    
    def get_current_step(self) -> Optional[Dict]:
        """获取当前步骤"""
        if 0 <= self.current_step_index < len(self.steps):
            step = self.steps[self.current_step_index].copy()
            # 替换步骤中的占位符
            if step.get("aiMessage"):
                step["aiMessage"] = step["aiMessage"].replace("{childName}", self.child_name)
            return step
        return None
    
    def get_next_step(self) -> Optional[Dict]:
        """获取下一步骤"""
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            self.completed_steps += 1
            self.current_retry_count = 0
            return self.get_current_step()
        return None
    
    def update_with_response(self, user_text: str, evaluation: Dict):
        """更新会话状态"""
        # 记录评估结果
        self.step_evaluations.append({
            "step_index": self.current_step_index,
            "user_text": user_text,
            "evaluation": evaluation,
            "timestamp": datetime.now().isoformat()
        })
        
        # 更新重试次数
        if evaluation.get("score", 0) < 60:  # 分数低于60分需要重试
            self.current_retry_count += 1
        else:
            self.current_retry_count = 0
    
    def should_proceed_to_next(self) -> bool:
        """判断是否应该进入下一步"""
        current_evaluation = self.step_evaluations[-1] if self.step_evaluations else None
        if not current_evaluation:
            return False
        
        # 如果分数达到要求或者重试次数用完，进入下一步
        score = current_evaluation["evaluation"].get("score", 0)
        return score >= 60 or self.current_retry_count >= self.max_retries
    
    def get_current_retry_count(self) -> int:
        """获取当前重试次数"""
        return self.current_retry_count
    
    def get_final_score(self) -> int:
        """计算最终分数"""
        if not self.step_evaluations:
            return 0
        
        total_score = 0
        for evaluation in self.step_evaluations:
            total_score += evaluation["evaluation"].get("score", 0)
        
        return int(total_score / len(self.step_evaluations))
