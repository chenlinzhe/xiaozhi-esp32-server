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
from config.logger import setup_logging


class ScenarioDialogueService:
    """场景对话服务"""
    
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging()
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
                self.logger.error(f"对话会话不存在: {session_id}")
                return {"success": False, "error": "对话会话不存在"}
            
            self.logger.info(f"处理用户回复 - 会话: {session_id}, 用户输入: {user_text}")
            
            # 评估用户回复
            evaluation = await self._evaluate_response(session, user_text)
            
            # 更新会话状态
            session.update_with_response(user_text, evaluation)
            
            # 获取回复进度信息
            reply_progress = session.get_reply_progress()
            
            # 检查是否应该显示预警
            if session.should_show_warning():
                self.logger.warning(f"触发回复次数预警 - 会话: {session_id}, 进度: {reply_progress}")
                # 标记预警已发送
                session.warning_sent = True
            
            # 检查是否超过用户回复次数限制
            if session.is_reply_limit_exceeded():
                # 超过回复次数限制，结束场景
                self.logger.warning(f"超过回复次数限制，结束场景 - 会话: {session_id}, 总回复次数: {session.get_total_user_replies()}")
                await self._complete_scenario(session)
                return {
                    "success": True,
                    "action": "completed",
                    "reason": "reply_limit_exceeded",
                    "evaluation": evaluation,
                    "final_score": session.get_final_score(),
                    "total_replies": session.get_total_user_replies(),
                    "max_replies": session.get_max_user_replies(),
                    "reply_progress": reply_progress,
                    "warning_message": session.get_warning_message()
                }
            
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
                        "evaluation": evaluation,
                        "total_replies": session.get_total_user_replies(),
                        "max_replies": session.get_max_user_replies(),
                        "reply_progress": reply_progress,
                        "warning_message": session.get_warning_message() if session.should_show_warning() else None
                    }
                else:
                    # 场景完成
                    self.logger.info(f"场景正常完成 - 会话: {session_id}")
                    await self._complete_scenario(session)
                    return {
                        "success": True,
                        "action": "completed",
                        "evaluation": evaluation,
                        "final_score": session.get_final_score(),
                        "total_replies": session.get_total_user_replies(),
                        "max_replies": session.get_max_user_replies(),
                        "reply_progress": reply_progress
                    }
            else:
                # 需要重试当前步骤
                current_step = session.get_current_step()
                return {
                    "success": True,
                    "action": "retry",
                    "current_step": current_step,
                    "evaluation": evaluation,
                    "retry_count": session.get_current_retry_count(),
                    "total_replies": session.get_total_user_replies(),
                    "max_replies": session.get_max_user_replies(),
                    "reply_progress": reply_progress,
                    "warning_message": session.get_warning_message() if session.should_show_warning() else None
                }
                
        except Exception as e:
            self.logger.error(f"处理用户回复失败 - 会话: {session_id}, 错误: {str(e)}", exc_info=True)
            # 即使出现异常，也要尝试记录回复次数
            try:
                session = self.current_sessions.get(session_id)
                if session:
                    session.total_user_replies += 1
                    self.logger.warning(f"异常情况下仍记录回复次数 - 会话: {session_id}, 总回复次数: {session.get_total_user_replies()}")
            except Exception as log_error:
                self.logger.error(f"记录异常回复次数失败: {str(log_error)}")
            
            return {
                "success": False, 
                "error": f"处理用户回复失败: {str(e)}",
                "total_replies": self.current_sessions.get(session_id, {}).get("total_user_replies", 0) if session_id in self.current_sessions else 0
            }
    
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
                "total_user_replies": session.get_total_user_replies(),
                "max_user_replies": session.get_max_user_replies(),
                "notes": f"场景学习完成，最终得分：{final_score}分，用户回复次数：{session.get_total_user_replies()}/{session.get_max_user_replies()}",
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
        
        reply_progress = session.get_reply_progress()
        
        return {
            "session_id": session.session_id,
            "scenario_name": session.scenario.get("scenarioName", ""),
            "current_step_index": session.current_step_index,
            "total_steps": len(session.steps),
            "completed_steps": session.completed_steps,
            "current_retry_count": session.get_current_retry_count(),
            "total_user_replies": session.get_total_user_replies(),
            "max_user_replies": session.get_max_user_replies(),
            "reply_progress": reply_progress,
            "warning_message": session.get_warning_message() if session.should_show_warning() else None,
            "start_time": session.start_time.isoformat(),
            "is_reply_limit_exceeded": session.is_reply_limit_exceeded()
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
        
        # 用户回复总次数统计
        self.total_user_replies = 0
        self.max_user_replies = scenario.get("maxUserReplies", 3)  # 从场景配置获取，默认3次
        
        # 回复次数预警机制
        self.warning_threshold = max(1, int(self.max_user_replies * 0.7))  # 70%时预警
        self.warning_sent = False
        
        # 记录每个步骤的评估结果
        self.step_evaluations = []
        
        # 初始化日志
        self.logger = setup_logging()
        self.logger.info(f"创建对话会话: {session_id}, 最大回复次数: {self.max_user_replies}, 预警阈值: {self.warning_threshold}")
    
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
        # 增加用户回复总次数
        self.total_user_replies += 1
        
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
        
        # 记录详细的回复统计信息
        self.logger.info(f"用户回复更新 - 会话: {self.session_id}, 总回复次数: {self.total_user_replies}/{self.max_user_replies}, "
                        f"当前步骤: {self.current_step_index}, 重试次数: {self.current_retry_count}, 分数: {evaluation.get('score', 0)}")
        
        # 检查预警条件
        if self.total_user_replies >= self.warning_threshold and not self.warning_sent:
            self.warning_sent = True
            self.logger.warning(f"回复次数预警 - 会话: {self.session_id}, 当前回复次数: {self.total_user_replies}, "
                              f"预警阈值: {self.warning_threshold}, 最大限制: {self.max_user_replies}")
        
        # 检查是否接近限制
        if self.total_user_replies >= self.max_user_replies - 1:
            self.logger.warning(f"即将达到回复次数限制 - 会话: {self.session_id}, 当前回复次数: {self.total_user_replies}, "
                              f"最大限制: {self.max_user_replies}")
    
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
    
    def is_reply_limit_exceeded(self) -> bool:
        """检查是否超过用户回复次数限制"""
        return self.total_user_replies >= self.max_user_replies
    
    def get_total_user_replies(self) -> int:
        """获取用户回复总次数"""
        return self.total_user_replies
    
    def get_max_user_replies(self) -> int:
        """获取用户回复次数限制"""
        return self.max_user_replies
    
    def get_reply_progress(self) -> Dict[str, any]:
        """获取回复进度信息"""
        progress_percentage = (self.total_user_replies / self.max_user_replies) * 100 if self.max_user_replies > 0 else 0
        remaining_replies = max(0, self.max_user_replies - self.total_user_replies)
        
        return {
            "current_replies": self.total_user_replies,
            "max_replies": self.max_user_replies,
            "remaining_replies": remaining_replies,
            "progress_percentage": round(progress_percentage, 1),
            "warning_threshold": self.warning_threshold,
            "warning_sent": self.warning_sent,
            "is_warning_active": self.total_user_replies >= self.warning_threshold,
            "is_limit_reached": self.is_reply_limit_exceeded()
        }
    
    def should_show_warning(self) -> bool:
        """判断是否应该显示预警信息"""
        return (self.total_user_replies >= self.warning_threshold and 
                not self.warning_sent and 
                not self.is_reply_limit_exceeded())
    
    def get_warning_message(self) -> str:
        """获取预警消息"""
        remaining = self.max_user_replies - self.total_user_replies
        if remaining <= 0:
            return "已达到最大回复次数限制，场景即将结束。"
        elif remaining == 1:
            return "这是最后一次回复机会，请认真回答。"
        else:
            return f"还有{remaining}次回复机会，请继续努力。"
    
    def get_final_score(self) -> int:
        """计算最终分数"""
        if not self.step_evaluations:
            return 0
        
        total_score = 0
        for evaluation in self.step_evaluations:
            total_score += evaluation["evaluation"].get("score", 0)
        
        return int(total_score / len(self.step_evaluations))
