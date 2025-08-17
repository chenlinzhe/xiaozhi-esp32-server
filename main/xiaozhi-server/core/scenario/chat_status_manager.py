"""
聊天状态管理器
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from core.utils.redis_client import get_redis_client
from core.scenario.dialogue_service import DialogueService
from config.logger import setup_logging


class ChatState(Enum):
    """聊天状态枚举 - 基于思维导图设计"""
    FREE_CHAT = "free_chat"                    # 自由聊天模式
    TEACHING_MODE = "teaching_mode"            # 教学模式
    WAITING_RESPONSE = "waiting_response"      # 等待用户响应
    EVALUATING = "evaluating"                  # 评估用户回复
    COMPLETED = "completed"                    # 教学完成


class ChatStatusManager:
    """聊天状态管理器"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.redis_client = get_redis_client()
        self.dialogue_service = DialogueService()
        
        # 模式切换关键词
        self.TEACHING_MODE_KEYWORDS = ["切换到教学模式", "教学模式", "开始教学"]
        self.FREE_MODE_KEYWORDS = ["切换到自由模式", "自由模式", "自由聊天"]
        
        # 等待时间配置（秒）- 使用动态配置，从API获取
        self.WAIT_TIME_MIN = 5
        self.WAIT_TIME_MAX = 20  # 默认最大等待时间，实际会从步骤配置中获取
        
        # 渐进式超时配置 - 仅作为默认值，实际超时时间从步骤配置获取
        self.PROGRESSIVE_TIMEOUT_CONFIG = {
            "enabled": True,              # 是否启用渐进式超时
            "warning_timeout": 0.7,       # 70%时间时发出警告
            "final_timeout": 0.9          # 90%时间时发出最终提醒
        }
        
        # 默认反馈消息 - 仅作为备用，优先使用场景配置中的消息
        self.DEFAULT_FEEDBACK_MESSAGES = {
            "encouragement_messages": [
                "没关系，我们再试一次！",
                "加油，你可以的！",
                "别着急，慢慢来~",
                "再想想看，我相信你！",
                "慢慢想，不着急~",
                "你可以的，再试一次！",
                "没关系，我们一起学习！"
            ],
            "praise_messages": [
                "太棒了！你说得很好！",
                "真聪明！回答得非常好！",
                "哇！你真是太厉害了！",
                "完美！你学得很快！",
                "太棒了！你回答得很准确！",
                "真棒！你理解得很好！",
                "太厉害了！你学得真快！"
            ],
            "warning_messages": [
                "还有一点时间，再想想看~",
                "别着急，慢慢想~",
                "再给你一点时间思考~",
                "加油，你可以的！",
                "再想想，我相信你！"
            ],
            "final_reminder_messages": [
                "马上时间就到了，再试试看~",
                "最后一点时间，加油！",
                "快想想看，我相信你！",
                "再试一次，你可以的！"
            ]
        }
    
    def is_mode_switch_command(self, user_text: str) -> Optional[str]:
        """判断是否为模式切换命令 - 基于思维导图优化
        
        Args:
            user_text: 用户输入的文本
            
        Returns:
            str: 目标模式 ("teaching_mode" 或 "free_mode")，如果不是切换命令返回None
        """
        user_text = user_text.strip()
        self.logger.debug(f"判断是否为模式切换命令: {user_text}")
        
        # 教学模式命令 - 扩展更多自然表达
        teaching_commands = [
            "教学模式", "教学", "学习模式", "学习", "开始教学", 
            "我要学习", "教我", "学习时间", "上课", "开始学习",
            "我想学习", "教我学习", "学习一下", "开始上课"
        ]
        
        # 自由模式命令 - 扩展更多自然表达
        free_commands = [
            "自由模式", "自由聊天", "聊天模式", "聊天", "结束教学",
            "不学了", "休息", "玩一会", "随便聊", "停止学习",
            "不想学了", "休息一下", "聊聊天", "玩一下"
        ]
        
        # 检查是否为教学模式命令
        if any(cmd in user_text for cmd in teaching_commands):
            self.logger.info(f"检测到教学模式切换命令: {user_text}")
            return "teaching_mode"
        elif any(cmd in user_text for cmd in free_commands):
            self.logger.info(f"检测到自由模式切换命令: {user_text}")
            return "free_mode"
        
        return None
    
    def _calculate_dynamic_timeout(self, step_difficulty: int = 1, user_age: int = 6, retry_count: int = 0) -> int:
        """计算动态超时时间 - 基于思维导图优化
        
        Args:
            step_difficulty: 步骤难度 (1-5)
            user_age: 用户年龄 (3-12)
            retry_count: 重试次数
            
        Returns:
            int: 超时时间（秒）
        """
        self.logger.info(f"=== 计算动态超时时间 ===")
        self.logger.info(f"步骤难度: {step_difficulty}")
        self.logger.info(f"用户年龄: {user_age}")
        self.logger.info(f"重试次数: {retry_count}")
        
        base_timeout = self.TIMEOUT_CONFIG["base_timeout"]
        difficulty_factor = step_difficulty * self.TIMEOUT_CONFIG["difficulty_factor"]
        age_factor = max(0, (6 - user_age) * self.TIMEOUT_CONFIG["age_factor"])
        retry_factor = retry_count * self.TIMEOUT_CONFIG["retry_factor"]
        
        self.logger.info(f"基础超时时间: {base_timeout}秒")
        self.logger.info(f"难度因子: {difficulty_factor}秒")
        self.logger.info(f"年龄因子: {age_factor}秒")
        self.logger.info(f"重试因子: {retry_factor}秒")
        
        total_timeout = base_timeout + difficulty_factor + age_factor + retry_factor
        self.logger.info(f"计算总超时时间: {total_timeout}秒")
        
        # 确保超时时间在合理范围内
        final_timeout = max(10, min(60, total_timeout))
        self.logger.info(f"最终超时时间: {final_timeout}秒")
        
        return final_timeout
    
    def _evaluate_response_enhanced(self, session: Dict, user_text: str) -> Dict:
        """增强的响应评估 - 基于思维导图优化
        
        Args:
            session: 会话数据
            user_text: 用户回复文本
            
        Returns:
            Dict: 评估结果
        """
        self.logger.info(f"=== 开始增强响应评估 ===")
        self.logger.info(f"用户输入: {user_text}")
        self.logger.info(f"会话数据: {session}")
        
        # 获取基础评估结果
        self.logger.info(f"调用基础评估函数")
        base_evaluation = self.dialogue_service._evaluate_response(session, user_text)
        self.logger.info(f"基础评估结果: {base_evaluation}")
        
        # 增强评估维度
        enhanced_evaluation = {
            **base_evaluation,
            "confidence": 0.0,           # 评估置信度
            "suggestions": [],           # 改进建议
            "next_action": "continue",   # 下一步动作
            "learning_progress": 0.0,    # 学习进度
            "engagement_level": 0.0      # 参与度
        }
        
        # 计算置信度（基于匹配质量）
        score = base_evaluation.get("score", 0)
        self.logger.info(f"基础分数: {score}")
        
        if score >= 90:
            enhanced_evaluation["confidence"] = 0.95
        elif score >= 80:
            enhanced_evaluation["confidence"] = 0.85
        elif score >= 60:
            enhanced_evaluation["confidence"] = 0.70
        else:
            enhanced_evaluation["confidence"] = 0.50
        
        self.logger.info(f"计算置信度: {enhanced_evaluation['confidence']}")
        
        # 生成改进建议
        if score < 60:
            enhanced_evaluation["suggestions"] = [
                "可以尝试更完整的表达",
                "注意关键词的使用",
                "可以多说一些细节"
            ]
        elif score < 80:
            enhanced_evaluation["suggestions"] = [
                "回答得很好，可以再详细一些",
                "尝试用更自然的表达方式"
            ]
        
        self.logger.info(f"生成改进建议: {enhanced_evaluation['suggestions']}")
        
        # 确定下一步动作
        if base_evaluation.get("is_excellent", False):
            enhanced_evaluation["next_action"] = "next_step"
        elif base_evaluation.get("is_good", False):
            enhanced_evaluation["next_action"] = "next_step"
        elif base_evaluation.get("retry_count", 0) >= self.ASSESSMENT_CONFIG["max_retries"]:
            enhanced_evaluation["next_action"] = "skip_step"
        else:
            enhanced_evaluation["next_action"] = "retry"
        
        self.logger.info(f"确定下一步动作: {enhanced_evaluation['next_action']}")
        
        # 计算学习进度
        current_step = session.get("current_step", 0)
        total_steps = session.get("total_steps", 1)
        enhanced_evaluation["learning_progress"] = (current_step / total_steps) * 100
        self.logger.info(f"学习进度: {enhanced_evaluation['learning_progress']}%")
        
        # 计算参与度（基于回复长度和内容）
        engagement_score = min(len(user_text) / 10, 1.0)  # 简单计算
        enhanced_evaluation["engagement_level"] = engagement_score
        self.logger.info(f"参与度: {enhanced_evaluation['engagement_level']}")
        
        self.logger.info(f"增强评估完成: {enhanced_evaluation}")
        return enhanced_evaluation
    
    def set_user_chat_status(self, user_id: str, status: str) -> bool:
        """设置用户聊天状态
        
        Args:
            user_id: 用户ID
            status: 聊天状态
            
        Returns:
            bool: 设置是否成功
        """
        return self.redis_client.set_chat_status(user_id, status)
    
    def get_user_chat_status(self, user_id: str) -> str:
        """获取用户聊天状态，默认为自由模式
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 聊天状态
        """
        status = self.redis_client.get_chat_status(user_id)
        return status if status else "free_mode"
    
    async def handle_user_input(self, user_id: str, user_text: str, 
                               child_name: str = "小朋友") -> Dict[str, Any]:
        """处理用户输入
        
        Args:
            user_id: 用户ID
            user_text: 用户输入的文本
            child_name: 儿童姓名
            
        Returns:
            Dict: 处理结果
        """
        try:
            self.logger.info(f"处理用户输入: user_id={user_id}, user_text={user_text[:50]}..., child_name={child_name}")
            
            # 检查是否为模式切换命令
            target_mode = self.is_mode_switch_command(user_text)
            if target_mode:
                self.logger.info(f"检测到模式切换命令: {target_mode}")
                # 切换模式
                success = self.set_user_chat_status(user_id, target_mode)
                if not success:
                    self.logger.error(f"设置用户 {user_id} 聊天状态失败")
                    return {
                        "success": False,
                        "error": "设置聊天状态失败"
                    }
                
                if target_mode == "teaching_mode":
                    self.logger.info("切换到教学模式，开始教学会话")
                    # 切换到教学模式时，直接开始教学会话并输出场景第一句话
                    return await self._start_teaching_session(user_id, child_name, from_mode_switch=True)
                else:
                    self.logger.info("切换到自由模式")
                    return {
                        "success": True,
                        "action": "mode_switch", 
                        "mode": "free_mode",
                        "ai_message": f"好的，{child_name}！现在进入自由聊天模式，我们可以随意聊天了。",
                        "message": "已切换到自由模式"
                    }
            
            # 获取当前聊天状态
            current_status = self.get_user_chat_status(user_id)
            self.logger.info(f"用户 {user_id} 当前聊天状态: {current_status}")
            
            if current_status == "teaching_mode":
                self.logger.info("当前为教学模式，处理教学逻辑")
                return await self._handle_teaching_mode(user_id, user_text, child_name)
            else:
                self.logger.info("当前为自由模式，继续正常流程")
                return await self._handle_free_mode(user_text, child_name)
                
        except Exception as e:
            self.logger.error(f"处理用户输入失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"处理用户输入失败: {str(e)}"
            }
    
    async def _handle_teaching_mode(self, user_id: str, user_text: str, 
                                   child_name: str) -> Dict[str, Any]:
        """处理教学模式
        
        Args:
            user_id: 用户ID
            user_text: 用户输入的文本
            child_name: 儿童姓名
            
        Returns:
            Dict: 处理结果
        """
        self.logger.info(f"处理教学模式: user_id={user_id}, user_text={user_text}, child_name={child_name}")
        
        # 获取或创建教学会话
        session_data = self.redis_client.get_session_data(f"teaching_{user_id}")
        
        if not session_data:
            self.logger.info("没有找到现有教学会话，创建新的教学会话")
            # 创建新的教学会话
            return await self._start_teaching_session(user_id, child_name)
        else:
            self.logger.info(f"找到现有教学会话: {session_data}")
            # 处理教学会话中的用户回复
            return await self._process_teaching_response(user_id, user_text, session_data, child_name)
    
    async def _start_teaching_session(self, user_id: str, child_name: str, from_mode_switch: bool = False) -> Dict[str, Any]:
        """开始教学会话
        
        Args:
            user_id: 用户ID
            child_name: 儿童姓名
            from_mode_switch: 是否从模式切换开始
            
        Returns:
            Dict: 处理结果
        """
        try:
            self.logger.info(f"开始教学会话: user_id={user_id}, child_name={child_name}, from_mode_switch={from_mode_switch}")
            
            # 获取默认教学场景
            self.logger.info("正在获取默认教学场景...")
            default_scenario = await self.dialogue_service.get_default_teaching_scenario()
            if default_scenario:
                self.logger.info(f"获取到默认教学场景: {default_scenario.get('scenarioName', 'Unknown')}")
            else:
                self.logger.warning("没有获取到默认教学场景，尝试获取第一个可用场景")
                # 如果没有默认教学场景，获取第一个可用场景
                scenarios = await self.dialogue_service.get_scenarios()
                self.logger.info(f"获取到 {len(scenarios) if scenarios else 0} 个场景")
                
                if not scenarios or len(scenarios) == 0:
                    self.logger.error("没有可用的教学场景")
                    return {
                        "success": False,
                        "error": "没有可用的教学场景，请联系管理员配置教学场景"
                    }
                default_scenario = scenarios[0]
                self.logger.info(f"使用第一个场景: {default_scenario.get('scenarioName', 'Unknown')}")
            
            # 使用数据库ID而不是scenarioId，因为API期望数字ID
            scenario_id = default_scenario.get("id")
            if not scenario_id:
                self.logger.error("场景配置错误，缺少场景ID")
                return {
                    "success": False,
                    "error": "场景配置错误，缺少场景ID"
                }
            
            self.logger.info(f"开始场景对话: scenario_id={scenario_id}")
            # 开始场景对话
            result = await self.dialogue_service.start_scenario(
                f"teaching_{user_id}", scenario_id, child_name
            )
            
            self.logger.info(f"场景对话结果: {result}")
            
            if result["success"]:
                # 保存会话数据
                session_data = {
                    "session_id": result["session_id"],
                    "scenario_id": scenario_id,
                    "scenario_name": result["scenario_name"],
                    "current_step": 0,
                    "total_steps": result["total_steps"],
                    "start_time": time.time(),
                    "waiting_for_response": True,
                    "wait_start_time": time.time(),
                    "evaluations": [] # 新增评估结果列表
                }
                
                self.logger.info(f"保存会话数据: {session_data}")
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                
                # 获取当前步骤的超时时间
                current_step = result["current_step"]
                timeout_seconds = current_step.get("timeoutSeconds", self.WAIT_TIME_MAX)
                self.logger.info(f"当前步骤超时时间: {timeout_seconds}秒")
                
                # 根据是否从模式切换开始，返回不同的action
                if from_mode_switch:
                    response = {
                        "success": True,
                        "action": "mode_switch",
                        "mode": "teaching_mode",
                        "session_id": result["session_id"],
                        "scenario_name": result["scenario_name"],
                        "ai_message": current_step.get("aiMessage", f"你好，{child_name}！"),
                        "message": f"已切换到教学模式，开始学习场景：{result['scenario_name']}",
                        "wait_time": timeout_seconds,  # 使用步骤配置的超时时间
                        "timeoutSeconds": timeout_seconds  # 同时传递超时时间
                    }
                else:
                    response = {
                        "success": True,
                        "action": "start_teaching",
                        "session_id": result["session_id"],
                        "scenario_name": result["scenario_name"],
                        "ai_message": current_step.get("aiMessage", f"你好，{child_name}！"),
                        "message": f"开始学习场景：{result['scenario_name']}",
                        "wait_time": timeout_seconds,  # 使用步骤配置的超时时间
                        "timeoutSeconds": timeout_seconds  # 同时传递超时时间
                    }
                
                self.logger.info(f"教学会话开始成功: {response}")
                return response
            else:
                self.logger.error(f"场景对话失败: {result}")
                return result
                
        except Exception as e:
            self.logger.error(f"开始教学会话失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"开始教学会话失败: {str(e)}"
            }
    
    async def _process_teaching_response(self, user_id: str, user_text: str, 
                                        session_data: Dict[str, Any], 
                                        child_name: str) -> Dict[str, Any]:
        """处理教学回复 - 优化版本"""
        try:
            self.logger.info(f"=== 开始处理教学回复 ===")
            self.logger.info(f"用户ID: {user_id}")
            self.logger.info(f"用户输入: {user_text}")
            self.logger.info(f"会话数据: {session_data}")
            self.logger.info(f"儿童姓名: {child_name}")
            
            # 获取当前步骤信息
            scenario_id = session_data.get("scenario_id")
            current_step_index = session_data.get("current_step", 0)
            self.logger.info(f"场景ID: {scenario_id}, 当前步骤索引: {current_step_index}")
            
            # 获取场景步骤
            self.logger.info(f"正在获取场景步骤: scenario_id={scenario_id}")
            steps = await self.dialogue_service._get_scenario_steps(scenario_id)
            self.logger.info(f"获取到 {len(steps) if steps else 0} 个场景步骤")
            
            if not steps or current_step_index >= len(steps):
                self.logger.error(f"场景步骤配置错误: steps={len(steps) if steps else 0}, current_step_index={current_step_index}")
                return {
                    "success": False,
                    "error": "场景步骤配置错误"
                }
            
            # 构建完整的session数据供评估使用
            full_session = {
                **session_data,
                "steps": steps,
                "child_name": child_name
            }
            self.logger.info(f"构建完整会话数据: {full_session}")
            
            current_step = steps[current_step_index]
            self.logger.info(f"当前步骤详情: {current_step}")
            
            # 智能评估用户回复
            self.logger.info(f"=== 开始智能评估 ===")
            self.logger.info(f"评估输入: user_text={user_text}")
            self.logger.info(f"评估会话: {full_session}")
            
            evaluation = self.dialogue_service._evaluate_response(full_session, user_text)
            score = evaluation["score"]
            
            self.logger.info(f"评估结果: {evaluation}")
            self.logger.info(f"评估分数: {score}")
            self.logger.info(f"是否优秀: {evaluation.get('is_excellent', False)}")
            self.logger.info(f"是否良好: {evaluation.get('is_good', False)}")
            self.logger.info(f"重试次数: {evaluation.get('retry_count', 0)}")
            
            # 记录评估结果
            session_data["evaluations"].append(evaluation)
            self.logger.info(f"已记录评估结果到会话数据")
            
            # 根据评估结果决定下一步
            self.logger.info(f"=== 根据评估结果决定下一步 ===")
            
            if evaluation["is_excellent"] or evaluation["is_good"]:
                self.logger.info(f"评估结果优秀或良好，准备进入下一步")
                # 优秀或良好，进入下一步
                session_data["current_step"] += 1
                session_data["waiting_for_response"] = False
                self.logger.info(f"更新步骤索引: {session_data['current_step']}")
                
                # 检查是否完成所有步骤
                if session_data["current_step"] >= len(steps):
                    self.logger.info(f"已完成所有步骤，教学结束")
                    # 教学完成
                    final_score = self.dialogue_service._calculate_final_score(session_data)
                    session_data["completed"] = True
                    session_data["final_score"] = final_score
                    self.logger.info(f"最终得分: {final_score}")
                    
                    # 保存会话数据
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    self.logger.info(f"已保存完成状态的会话数据")
                    
                    # 生成完成消息
                    completion_message = self._generate_completion_message(final_score, child_name)
                    self.logger.info(f"生成完成消息: {completion_message}")
                    
                    result = {
                        "success": True,
                        "action": "completed",
                        "session_id": f"teaching_{user_id}",
                        "ai_message": completion_message,
                        "final_score": final_score,
                        "evaluation": evaluation,
                        "message": f"教学完成！最终得分：{final_score}分"
                    }
                    self.logger.info(f"返回完成结果: {result}")
                    return result
                else:
                    self.logger.info(f"进入下一步，步骤索引: {session_data['current_step']}")
                    # 进入下一步
                    next_step = steps[session_data["current_step"]]
                    ai_message = next_step.get("aiMessage", "")
                    if ai_message:
                        ai_message = ai_message.replace("{文杰}", child_name)
                    
                    self.logger.info(f"下一步AI消息: {ai_message}")
                    
                    # 保存会话数据
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    self.logger.info(f"已保存会话数据")
                    
                    result = {
                        "success": True,
                        "action": "next_step",
                        "session_id": f"teaching_{user_id}",
                        "ai_message": ai_message,
                        "current_step": next_step,
                        "evaluation": evaluation,
                        "message": f"进入下一步：{evaluation['feedback']}",
                        "timeoutSeconds": self.WAIT_TIME_MAX
                    }
                    self.logger.info(f"返回下一步结果: {result}")
                    return result
            else:
                self.logger.info(f"评估结果需要重试")
                # 需要重试
                retry_count = evaluation["retry_count"]
                self.logger.info(f"当前重试次数: {retry_count}, 最大重试次数: {self.ASSESSMENT_CONFIG['max_retries']}")
                
                # 检查是否超过最大重试次数
                if retry_count >= self.ASSESSMENT_CONFIG["max_retries"]:
                    self.logger.info(f"超过最大重试次数，跳过当前步骤")
                    # 超过重试次数，使用替代消息
                    alternative_message = evaluation.get("alternative_message", "")
                    if not alternative_message:
                        alternative_message = "让我来告诉你正确答案。"
                    
                    self.logger.info(f"替代消息: {alternative_message}")
                    
                    # 进入下一步（跳过当前步骤）
                    session_data["current_step"] += 1
                    session_data["waiting_for_response"] = False
                    self.logger.info(f"更新步骤索引: {session_data['current_step']}")
                    
                    # 保存会话数据
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    self.logger.info(f"已保存会话数据")
                    
                    result = {
                        "success": True,
                        "action": "next_step",
                        "session_id": f"teaching_{user_id}",
                        "ai_message": alternative_message,
                        "evaluation": evaluation,
                        "message": "使用替代消息继续",
                        "timeoutSeconds": self.WAIT_TIME_MAX
                    }
                    self.logger.info(f"返回跳过步骤结果: {result}")
                    return result
                else:
                    self.logger.info(f"继续重试当前步骤")
                    # 继续重试当前步骤
                    session_data["waiting_for_response"] = False
                    
                    # 保存会话数据
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    self.logger.info(f"已保存会话数据")
                    
                    # 使用替代消息或原消息重试
                    retry_message = evaluation.get("alternative_message", "")
                    if not retry_message:
                        retry_message = current_step.get("aiMessage", "")
                        if retry_message:
                            retry_message = retry_message.replace("{文杰}", child_name)
                    
                    self.logger.info(f"重试消息: {retry_message}")
                    
                    result = {
                        "success": True,
                        "action": "retry",
                        "session_id": f"teaching_{user_id}",
                        "ai_message": retry_message,
                        "current_step": current_step,
                        "evaluation": evaluation,
                        "message": f"重试：{evaluation['feedback']}",
                        "timeoutSeconds": self.WAIT_TIME_MAX
                    }
                    self.logger.info(f"返回重试结果: {result}")
                    return result
                    
        except Exception as e:
            self.logger.error(f"处理教学回复失败: {e}")
            return {
                "success": False,
                "error": f"处理教学回复失败: {str(e)}"
            }
    
    def _generate_completion_message(self, final_score: int, child_name: str) -> str:
        """生成教学完成消息"""
        self.logger.info(f"=== 生成教学完成消息 ===")
        self.logger.info(f"最终得分: {final_score}")
        self.logger.info(f"儿童姓名: {child_name}")
        
        if final_score >= 90:
            message = f"太棒了，{child_name}！你完成了所有的学习任务，表现非常优秀！"
        elif final_score >= 80:
            message = f"很好，{child_name}！你完成了学习任务，表现很棒！"
        elif final_score >= 60:
            message = f"不错，{child_name}！你完成了学习任务，继续加油！"
        else:
            message = f"没关系，{child_name}！学习是一个过程，下次会更好的！"
        
        self.logger.info(f"生成的完成消息: {message}")
        return message
    
    async def _handle_free_mode(self, user_text: str, child_name: str) -> Dict[str, Any]:
        """处理自由模式
        
        Args:
            user_text: 用户输入的文本
            child_name: 儿童姓名
            
        Returns:
            Dict: 处理结果，自由模式下返回None让正常流程继续
        """
        # 自由模式下，不进行特殊处理，让正常的LLM对话流程继续
        return None
    
    async def check_teaching_timeout(self, user_id: str) -> Optional[Dict[str, Any]]:
        """检查教学会话是否超时 - 优化版本，支持渐进式提示
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 超时处理结果，如果没有超时返回None
        """
        self.logger.info(f"=== 检查教学超时（优化版） ===")
        self.logger.info(f"用户ID: {user_id}")
        
        session_data = self.redis_client.get_session_data(f"teaching_{user_id}")
        self.logger.info(f"会话数据: {session_data}")
        
        if not session_data or not session_data.get("waiting_for_response"):
            self.logger.info(f"没有等待响应的会话，无需检查超时")
            return None
        
        wait_start_time = session_data.get("wait_start_time", 0)
        current_time = time.time()
        wait_duration = current_time - wait_start_time
        timeout_seconds = session_data.get("timeout_seconds", self.WAIT_TIME_MAX)
        
        self.logger.info(f"等待开始时间: {wait_start_time}")
        self.logger.info(f"当前时间: {current_time}")
        self.logger.info(f"等待时长: {wait_duration}秒")
        self.logger.info(f"超时时间: {timeout_seconds}秒")
        
        # 检查渐进式提示
        if self.PROGRESSIVE_TIMEOUT_CONFIG.get("enabled", False):
            warning_threshold = timeout_seconds * self.PROGRESSIVE_TIMEOUT_CONFIG["warning_timeout"]
            final_threshold = timeout_seconds * self.PROGRESSIVE_TIMEOUT_CONFIG["final_timeout"]
            
            # 检查是否需要发出警告提示
            if (wait_duration >= warning_threshold and 
                not session_data.get("warning_sent", False)):
                self.logger.info(f"发出警告提示（{wait_duration}秒 >= {warning_threshold}秒）")
                session_data["warning_sent"] = True
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                
                warning_message = self._get_random_message(self.DEFAULT_FEEDBACK_MESSAGES["warning_messages"])
                child_name = session_data.get("child_name", "小朋友")
                warning_message = warning_message.replace("{文杰}", child_name)
                
                return {
                    "success": True,
                    "action": "warning_reminder",
                    "ai_message": warning_message,
                    "message": "发出警告提示"
                }
            
            # 检查是否需要发出最终提醒
            elif (wait_duration >= final_threshold and 
                  not session_data.get("final_reminder_sent", False)):
                self.logger.info(f"发出最终提醒（{wait_duration}秒 >= {final_threshold}秒）")
                session_data["final_reminder_sent"] = True
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                
                final_message = self._get_random_message(self.DEFAULT_FEEDBACK_MESSAGES["final_reminder_messages"])
                child_name = session_data.get("child_name", "小朋友")
                final_message = final_message.replace("{文杰}", child_name)
                
                return {
                    "success": True,
                    "action": "final_reminder",
                    "ai_message": final_message,
                    "message": "发出最终提醒"
                }
        
        # 检查是否超过等待时间
        if wait_duration >= timeout_seconds:
            self.logger.info(f"检测到超时，开始处理超时逻辑")
            # 超时，获取当前步骤的替代消息
            scenario_id = session_data.get("scenario_id")
            current_step = session_data.get("current_step", 0)
            self.logger.info(f"场景ID: {scenario_id}, 当前步骤: {current_step}")
            
            # 获取当前步骤的详细信息
            steps = await self.dialogue_service._get_scenario_steps(scenario_id)
            if steps and current_step < len(steps):
                current_step_data = steps[current_step]
                self.logger.info(f"当前步骤数据: {current_step_data}")
                
                # 优先使用auto_reply_on_timeout，如果没有则使用alternative_message
                auto_reply = current_step_data.get("autoReplyOnTimeout")
                alternative_message = current_step_data.get("alternativeMessage")
                
                self.logger.info(f"自动回复消息: {auto_reply}")
                self.logger.info(f"替代消息: {alternative_message}")
                
                # 优化超时消息，增加鼓励性
                if auto_reply:
                    timeout_message = auto_reply
                elif alternative_message:
                    timeout_message = f"没关系，让我来示范一下：{alternative_message}"
                else:
                    timeout_message = "时间到了，让我来示范一下正确的回答。"
                
                # 替换儿童姓名占位符
                child_name = session_data.get("child_name", "小朋友")
                if timeout_message:
                    timeout_message = timeout_message.replace("{文杰}", child_name)
            else:
                self.logger.warning(f"无法获取步骤数据，使用默认超时消息")
                timeout_message = "时间到了，让我来示范一下正确的回答。"
            
            self.logger.info(f"最终超时消息: {timeout_message}")
            
            # 更新会话状态
            session_data["waiting_for_response"] = False
            session_data["warning_sent"] = False
            session_data["final_reminder_sent"] = False
            self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
            self.logger.info(f"已更新会话状态")
            
            result = {
                "success": True,
                "action": "timeout_response",
                "ai_message": timeout_message,
                "message": "用户超时，使用替代消息回复"
            }
            self.logger.info(f"返回超时处理结果: {result}")
            return result
        else:
            self.logger.info(f"未超时，等待时长: {wait_duration}秒 < {timeout_seconds}秒")
        
        return None
    
    def _get_random_message(self, messages: List[str]) -> str:
        """从消息列表中随机选择一条消息
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 随机选择的消息
        """
        import random
        return random.choice(messages) if messages else "加油！"
