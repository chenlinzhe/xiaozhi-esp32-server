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
import json


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
        self.WAIT_TIME_MIN = 60
        self.WAIT_TIME_MAX = 60  # 默认最大等待时间，实际会从步骤配置中获取
        
        # 渐进式超时配置 - 仅作为默认值，实际超时时间从步骤配置获取
        self.PROGRESSIVE_TIMEOUT_CONFIG = {
            "enabled": True,              # 是否启用渐进式超时
            "warning_timeout": 0.4,       # 70%时间时发出警告
            "final_timeout": 0.7          # 90%时间时发出最终提醒
        }
        
        # 超时配置
        self.TIMEOUT_CONFIG = {
            "base_timeout": 40,           # 基础超时时间
            "min_timeout": 20,            # 最小超时时间
            "max_timeout": 120,            # 最大超时时间
            "difficulty_factor": 2,       # 难度因子
            "age_factor": 3,              # 年龄因子
            "retry_factor": 5             # 重试因子
        }
        
        # 评估配置
        self.ASSESSMENT_CONFIG = {
            "max_retries": 3,             # 最大重试次数
            "pass_threshold": 60,         # 及格分数线
            "good_threshold": 80,         # 良好分数线
            "excellent_threshold": 90     # 优秀分数线
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
    
    def clear_user_chat_status(self, user_id: str) -> bool:
        """清理用户聊天状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 清理是否成功
        """
        try:
            result = self.redis_client.delete_chat_status(user_id)
            if result:
                self.logger.info(f"成功清理用户 {user_id} 的聊天状态")
            else:
                self.logger.warning(f"用户 {user_id} 的聊天状态不存在或清理失败")
            return result
        except Exception as e:
            self.logger.error(f"清理用户聊天状态失败: {e}")
            return False
    
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
            self.logger.info(f"处理用户输入: user_id={user_id}, user_text={user_text}, child_name={child_name}")
            
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
            default_scenario = self.dialogue_service.get_default_teaching_scenario()
            print(f"默认教学场景获取结果: {default_scenario}")
            
            if default_scenario:
                self.logger.info(f"获取到默认教学场景: {default_scenario.get('scenarioName', 'Unknown')}")
                print(f"默认场景详情:")
                print(f"  - 场景ID: {default_scenario.get('id', 'N/A')}")
                print(f"  - 场景名称: {default_scenario.get('scenarioName', 'N/A')}")
                print(f"  - 是否活跃: {default_scenario.get('isActive', 'N/A')}")
                print(f"  - 代理ID: {default_scenario.get('agentId', 'N/A')}")
                print(f"  - 是否默认教学: {default_scenario.get('isDefaultTeaching', 'N/A')}")
                print(f"  - 创建时间: {default_scenario.get('createTime', 'N/A')}")
                print(f"  - 更新时间: {default_scenario.get('updateTime', 'N/A')}")
                print(f"  - 完整默认场景数据: {default_scenario}")
            else:
                self.logger.warning("没有获取到默认教学场景，尝试获取第一个可用场景")
                # 如果没有默认教学场景，获取第一个可用场景
                scenarios = self.dialogue_service.get_scenarios()
                print(f"获取到的所有场景: {scenarios}")
                self.logger.info(f"获取到 {len(scenarios) if scenarios else 0} 个场景")
                
                if not scenarios or len(scenarios) == 0:
                    self.logger.error("没有可用的教学场景")
                    return {
                        "success": False,
                        "error": "没有可用的教学场景，请联系管理员配置教学场景"
                    }
                default_scenario = scenarios[0]
                print(f"选择第一个场景详情:")
                print(f"  - 场景ID: {default_scenario.get('id', 'N/A')}")
                print(f"  - 场景名称: {default_scenario.get('scenarioName', 'N/A')}")
                print(f"  - 是否活跃: {default_scenario.get('isActive', 'N/A')}")
                print(f"  - 代理ID: {default_scenario.get('agentId', 'N/A')}")
                print(f"  - 是否默认教学: {default_scenario.get('isDefaultTeaching', 'N/A')}")
                print(f"  - 创建时间: {default_scenario.get('createTime', 'N/A')}")
                print(f"  - 更新时间: {default_scenario.get('updateTime', 'N/A')}")
                print(f"  - 完整第一个场景数据: {default_scenario}")
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
                    "wait_start_time": None,  # 初始化为None，在TTS消息发送完成后设置
                    "evaluations": [], # 新增评估结果列表
                    "total_user_replies": 0,  # 用户回复总次数统计
                    "max_user_replies": default_scenario.get("maxUserReplies", 3),  # 从场景配置获取，默认3次
                    "warning_sent": False,  # 预警是否已发送
                    "completion_reason": None,  # 完成原因
                    "step_retry_counts": {},  # 每个步骤的重试计数 {step_index: retry_count}
                    "current_step_retry_count": 0  # 当前步骤的重试计数
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
                        "timeoutSeconds": timeout_seconds,  # 同时传递超时时间
                        "current_step": current_step  # 传递完整的步骤对象
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
                        "timeoutSeconds": timeout_seconds,  # 同时传递超时时间
                        "current_step": current_step  # 传递完整的步骤对象
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
    
    def update_wait_start_time(self, user_id: str):
        """更新等待开始时间（在TTS消息发送完成后调用）"""
        try:
            session_data = self.redis_client.get_session_data(f"teaching_{user_id}")
            if session_data and session_data.get("waiting_for_response"):
                session_data["wait_start_time"] = time.time()
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                self.logger.info(f"更新用户 {user_id} 的等待开始时间: {session_data['wait_start_time']}")
        except Exception as e:
            self.logger.error(f"更新等待开始时间失败: {e}")

    async def _process_teaching_response(self, user_id: str, user_text: str, 
                                        session_data: Dict[str, Any], 
                                        child_name: str) -> Dict[str, Any]:
        """处理教学回复 - 优化版本，实现完整的步骤配置处理流程"""
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
            # self.logger.info(f"构建完整会话数据: {full_session}")
            
            current_step = steps[current_step_index]
            self.logger.info(f"当前步骤详情: {current_step}")
            
            # 智能评估用户回复
            self.logger.info(f"=== 开始智能评估 ===")
            self.logger.info(f"评估输入: user_text={user_text}")
            # self.logger.info(f"评估会话: {full_session}")
            
            evaluation = self._evaluate_response_with_config(current_step, user_text, session_data)
            score = evaluation["score"]
            
            self.logger.info(f"评估结果: {evaluation}")
            self.logger.info(f"评估分数: {score}")
            self.logger.info(f"是否通过: {evaluation.get('is_passed', False)}")
            self.logger.info(f"重试次数: {evaluation.get('retry_count', 0)}")
            
            # 记录评估结果
            session_data["evaluations"].append(evaluation)
            self.logger.info(f"已记录评估结果到会话数据")
            
            # 更新用户回复次数统计
            session_data["total_user_replies"] = session_data.get("total_user_replies", 0) + 1
            current_replies = session_data["total_user_replies"]
            
            # 获取当前步骤的最大尝试次数（优先步骤配置，备用场景配置）
            step_max_attempts = self._get_step_max_attempts(current_step, session_data)
            current_step_retry_count = session_data.get("current_step_retry_count", 0)
            
            # 判断是否为叶子节点
            is_leaf_step = self._is_leaf_step(current_step)
            
            self.logger.info(f"步骤最大尝试次数: {step_max_attempts}")
            self.logger.info(f"当前步骤重试次数: {current_step_retry_count}")
            self.logger.info(f"是否为叶子节点: {is_leaf_step}")
            self.logger.info(f"用户总回复次数: {current_replies}")
            
            # 对于叶子节点，检查是否超过步骤最大尝试次数
            if is_leaf_step and current_step_retry_count >= step_max_attempts:
                self.logger.warning(f"叶子节点超过最大尝试次数，结束教学 - 用户: {user_id}, 重试次数: {current_step_retry_count}/{step_max_attempts}")
                # 叶子节点超过最大尝试次数，结束教学
                final_score = self._calculate_final_score(session_data)
                session_data["completed"] = True
                session_data["final_score"] = final_score
                session_data["completion_reason"] = "leaf_step_max_attempts_exceeded"
                
                # 保存会话数据
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                
                # 切换到自由模式
                self.set_user_chat_status(user_id, "free_mode")
                
                return {
                    "success": True,
                    "action": "completed",
                    "reason": "leaf_step_max_attempts_exceeded",
                    "ai_message": f"你已经尝试了{current_step_retry_count}次，达到了最大尝试次数限制。教学结束，最终得分：{final_score}分。",
                    "final_score": final_score,
                    "total_attempts": current_step_retry_count,
                    "max_attempts": step_max_attempts
                }
            
            # 对于非叶子节点，检查场景级别的回复次数限制
            max_user_replies = session_data.get("max_user_replies", 3)
            if current_replies >= max_user_replies:
                self.logger.warning(f"超过场景回复次数限制，结束教学 - 用户: {user_id}, 回复次数: {current_replies}/{max_user_replies}")
                # 教学因回复次数限制结束
                final_score = self._calculate_final_score(session_data)
                session_data["completed"] = True
                session_data["final_score"] = final_score
                session_data["completion_reason"] = "reply_limit_exceeded"
                
                # 保存会话数据
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                
                # 切换到自由模式
                self.set_user_chat_status(user_id, "free_mode")
                
                return {
                    "success": True,
                    "action": "completed",
                    "reason": "reply_limit_exceeded",
                    "ai_message": f"你已经回复了{current_replies}次，达到了最大回复次数限制。教学结束，最终得分：{final_score}分。",
                    "final_score": final_score,
                    "total_replies": current_replies,
                    "max_replies": max_user_replies
                }
            
            # 检查是否应该显示预警
            warning_threshold = max(1, int(max_user_replies * 0.7))  # 70%时预警
            warning_message = None
            if current_replies >= warning_threshold and not session_data.get("warning_sent", False):
                session_data["warning_sent"] = True
                remaining = max_user_replies - current_replies
                warning_message = f"注意：你已经回复了{current_replies}次，还有{remaining}次机会。"
                self.logger.warning(f"触发回复次数预警 - 用户: {user_id}, 当前: {current_replies}, 剩余: {remaining}")
            
            # 根据评估结果决定下一步 - 区分叶子节点和非叶子节点
            self.logger.info(f"=== 根据评估结果决定下一步 ===")
            self.logger.info(f"评估分数: {score}")
            self.logger.info(f"是否通过: {evaluation.get('is_passed', False)}")
            self.logger.info(f"是否为叶子节点: {is_leaf_step}")
            
            if is_leaf_step:
                # 叶子节点处理：根据评估结果决定是否重试或结束
                self.logger.info(f"处理叶子节点逻辑")
                
                if evaluation.get('is_passed', False):
                    # 叶子节点通过，结束教学
                    self.logger.info(f"叶子节点通过，结束教学")
                    final_score = self._calculate_final_score(session_data)
                    session_data["completed"] = True
                    session_data["final_score"] = final_score
                    session_data["completion_reason"] = "leaf_step_passed"
                    
                    # 保存会话数据
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    
                    # 切换到自由模式
                    self.set_user_chat_status(user_id, "free_mode")
                    
                    return {
                        "success": True,
                        "action": "completed",
                        "reason": "leaf_step_passed",
                        "ai_message": f"太棒了！你完成了学习任务，最终得分：{final_score}分。",
                        "final_score": final_score
                    }
                else:
                    # 叶子节点未通过，增加重试次数
                    session_data["current_step_retry_count"] = current_step_retry_count + 1
                    self.logger.info(f"叶子节点未通过，增加重试次数: {session_data['current_step_retry_count']}/{step_max_attempts}")
                    
                    # 检查是否超过最大尝试次数
                    if session_data["current_step_retry_count"] >= step_max_attempts:
                        self.logger.warning(f"叶子节点超过最大尝试次数，结束教学")
                        final_score = self._calculate_final_score(session_data)
                        session_data["completed"] = True
                        session_data["final_score"] = final_score
                        session_data["completion_reason"] = "leaf_step_max_attempts_exceeded"
                        
                        # 保存会话数据
                        self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                        
                        # 切换到自由模式
                        self.set_user_chat_status(user_id, "free_mode")
                        
                        return {
                            "success": True,
                            "action": "completed",
                            "reason": "leaf_step_max_attempts_exceeded",
                            "ai_message": f"你已经尝试了{current_step_retry_count + 1}次，达到了最大尝试次数限制。教学结束，最终得分：{final_score}分。",
                            "final_score": final_score,
                            "total_attempts": current_step_retry_count + 1,
                            "max_attempts": step_max_attempts
                        }
                    else:
                        # 继续重试当前步骤
                        self.logger.info(f"叶子节点继续重试当前步骤")
                        session_data["waiting_for_response"] = True
                        session_data["wait_start_time"] = time.time()
                        session_data["warning_sent"] = False
                        session_data["final_reminder_sent"] = False
                        
                        # 保存会话数据
                        self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                        
                        return {
                            "success": True,
                            "action": "retry_current_step",
                            "session_id": f"teaching_{user_id}",
                            "current_step": current_step,
                            "evaluation": evaluation,
                            "message": f"让我们再试一次：{evaluation['feedback']}",
                            "timeoutSeconds": current_step.get("timeoutSeconds", self.WAIT_TIME_MAX),
                            "retry_count": session_data["current_step_retry_count"],
                            "max_attempts": step_max_attempts,
                            "is_leaf_step": True
                        }
            else:
                # 非叶子节点处理：使用分支配置
                self.logger.info(f"处理非叶子节点逻辑")
                
                # 根据评估分数和成功条件分支配置决定跳转
                next_step_id = None
                branch_type = None
                
                if score >= 90:
                    # 完全匹配分支 (分数 >= 90)
                    next_step_id = current_step.get("perfectMatchNextStepId") or current_step.get("exactMatchStepId")
                    branch_type = "perfect_match"
                    self.logger.info(f"完全匹配分支，跳转步骤ID: {next_step_id}")
                elif score >= 60:
                    # 部分匹配分支 (60 <= 分数 < 90)
                    next_step_id = current_step.get("partialMatchNextStepId") or current_step.get("partialMatchStepId")
                    branch_type = "partial_match"
                    self.logger.info(f"部分匹配分支，跳转步骤ID: {next_step_id}")
                else:
                    # 完全不匹配分支 (分数 < 60)
                    next_step_id = current_step.get("noMatchNextStepId") or current_step.get("noMatchStepId")
                    branch_type = "no_match"
                    self.logger.info(f"完全不匹配分支，跳转步骤ID: {next_step_id}")
                
                # 重置当前步骤重试次数（进入新步骤时重置）
                session_data["current_step_retry_count"] = 0
            
            # 根据分支配置决定跳转
            if next_step_id:
                self.logger.info(f"根据{branch_type}分支配置，跳转到步骤ID: {next_step_id}")
                # 查找指定的下一步骤
                next_step_index = self._find_step_by_id(steps, next_step_id)
                if next_step_index is not None:
                    session_data["current_step"] = next_step_index
                    self.logger.info(f"跳转到指定步骤: {next_step_index}")
                else:
                    # 如果找不到指定的步骤，尝试回退到下一个步骤
                    current_step_index = session_data.get("current_step", 0)
                    next_step_index = current_step_index + 1
                    
                    if next_step_index < len(steps):
                        self.logger.warning(f"未找到指定的下一步骤ID: {next_step_id}，回退到下一个步骤: {next_step_index}")
                        session_data["current_step"] = next_step_index
                        self.logger.info(f"回退跳转到下一个步骤: {next_step_index}")
                    else:
                        self.logger.warning(f"未找到指定的下一步骤ID: {next_step_id}，且已到达最后一个步骤，教学结束")
                        # 如果找不到指定的步骤且已到达最后一个步骤，结束教学
                        final_score = self._calculate_final_score(session_data)
                        session_data["completed"] = True
                        session_data["final_score"] = final_score
                        session_data["completion_reason"] = "branch_step_not_found"
                        
                        # 保存会话数据
                        self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                        
                        # 切换到自由模式
                        self.set_user_chat_status(user_id, "free_mode")
                        
                        return {
                            "success": True,
                            "action": "completed",
                            "reason": "branch_step_not_found",
                            "ai_message": f"教学完成，最终得分：{final_score}分。",
                            "final_score": final_score
                        }
            else:
                # 没有配置分支跳转，结束教学
                self.logger.warning(f"没有配置{branch_type}分支跳转，教学结束")
                final_score = self._calculate_final_score(session_data)
                session_data["completed"] = True
                session_data["final_score"] = final_score
                session_data["completion_reason"] = "no_branch_config"
                
                # 保存会话数据
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                
                # 切换到自由模式
                self.set_user_chat_status(user_id, "free_mode")
                
                return {
                    "success": True,
                    "action": "completed",
                    "reason": "no_branch_config",
                    "ai_message": f"教学完成，最终得分：{final_score}分。",
                    "final_score": final_score
                }
            
            # 设置等待响应状态
            session_data["waiting_for_response"] = True
            session_data["wait_start_time"] = time.time()
            session_data["warning_sent"] = False
            session_data["final_reminder_sent"] = False
            session_data["retry_count"] = 0  # 重置重试次数
            self.logger.info(f"更新步骤索引: {session_data['current_step']}")
            self.logger.info(f"设置等待响应状态: waiting_for_response=True, wait_start_time={session_data['wait_start_time']}")
            
            # 检查是否完成所有步骤
            if session_data["current_step"] >= len(steps):
                self.logger.info(f"已完成所有步骤，教学结束")
                # 教学完成
                final_score = self._calculate_final_score(session_data)
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
                # 不再使用AI消息，直接进入下一步
                self.logger.info(f"进入下一步，步骤: {next_step.get('stepName', '未知步骤')}")
                
                # 获取下一步的超时时间
                timeout_seconds = next_step.get("timeoutSeconds", self.WAIT_TIME_MAX)
                self.logger.info(f"下一步超时时间: {timeout_seconds}秒")
                
                # 保存会话数据
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                self.logger.info(f"已保存会话数据")
                
                # 构建回复进度信息
                reply_progress = {
                    "current_replies": current_replies,
                    "max_replies": max_user_replies,
                    "remaining_replies": max_user_replies - current_replies,
                    "progress_percentage": round((current_replies / max_user_replies) * 100, 1) if max_user_replies > 0 else 0,
                    "warning_threshold": warning_threshold,
                    "warning_sent": session_data.get("warning_sent", False),
                    "is_warning_active": current_replies >= warning_threshold,
                    "is_limit_reached": current_replies >= max_user_replies
                }
                
                # 根据分支类型确定action
                if branch_type == "perfect_match":
                    action = "perfect_match_next"
                elif branch_type == "partial_match":
                    action = "partial_match_next"
                elif branch_type == "no_match":
                    action = "no_match_next"
                else:
                    action = "next_step"
                
                result = {
                    "success": True,
                    "action": action,
                    "session_id": f"teaching_{user_id}",
                    "current_step": next_step,
                    "evaluation": evaluation,
                    "message": f"根据{branch_type}分支进入下一步：{evaluation['feedback']}",
                    "timeoutSeconds": timeout_seconds,
                    "total_replies": current_replies,
                    "max_replies": max_user_replies,
                    "reply_progress": reply_progress,
                    "warning_message": warning_message,
                    "branch_type": branch_type
                }
                self.logger.info(f"返回下一步结果: {result}")
                return result
            # 注意：移除了重试逻辑，现在用户回复后直接进入下一步
                    
        except Exception as e:
            self.logger.error(f"处理教学回复失败: {e}", exc_info=True)
            # 即使出现异常，也要尝试记录回复次数
            try:
                session_data = self.redis_client.get_session_data(f"teaching_{user_id}")
                if session_data:
                    session_data["total_user_replies"] = session_data.get("total_user_replies", 0) + 1
                    self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                    self.logger.warning(f"异常情况下仍记录回复次数 - 用户: {user_id}, 总回复次数: {session_data.get('total_user_replies', 0)}")
            except Exception as log_error:
                self.logger.error(f"记录异常回复次数失败: {str(log_error)}")
            
            return {
                "success": False,
                "error": f"处理教学回复失败: {str(e)}",
                "total_replies": session_data.get("total_user_replies", 0) if 'session_data' in locals() else 0
            }

    # # def _evaluate_response_with_config(self, step_config: Dict, user_text: str, session_data: Dict) -> Dict:
    #     """根据步骤配置评估用户回复
        
    #     Args:
    #         step_config: 步骤配置
    #         user_text: 用户输入文本
    #         session_data: 会话数据
            
    #     Returns:
    #         Dict: 评估结果
    #     """
    #     self.logger.info(f"=== 根据步骤配置评估用户回复 ===")
    #     self.logger.info(f"步骤配置: {step_config}")
    #     self.logger.info(f"用户输入: {user_text}")
        
    #     # 获取配置参数
    #     success_condition = ""
    #     expected_keywords_str = step_config.get("expectedKeywords", "")
    #     expected_phrases_str = step_config.get("expectedPhrases", "")
    #     max_attempts = step_config.get("maxAttempts", 3)
    #     retry_count = session_data.get("retry_count", 0)
        
    #     self.logger.info(f"成功条件: {success_condition}")
    #     self.logger.info(f"期望关键词: {expected_keywords_str}")
    #     self.logger.info(f"期望短语: {expected_phrases_str}")
    #     self.logger.info(f"最大尝试次数: {max_attempts}")
    #     self.logger.info(f"当前重试次数: {retry_count}")
        
    #     # 解析期望关键词和短语
    #     expected_keywords = self._parse_json_list(expected_keywords_str)
    #     expected_phrases = self._parse_json_list(expected_phrases_str)
        
    #     self.logger.info(f"解析后的期望关键词: {expected_keywords}")
    #     self.logger.info(f"解析后的期望短语: {expected_phrases}")
        
    #     # 获取配置中的鼓励话语
    #     praise_message = step_config.get("praiseMessage", "")
    #     encouragement_message = step_config.get("encouragementMessage", "")
        
    #     # 替换儿童姓名占位符
    #     child_name = session_data.get("child_name", "小朋友")
    #     if praise_message:
    #         praise_message = praise_message.replace("{childName}", child_name)
    #         praise_message = praise_message.replace("{文杰}", child_name)
    #     if encouragement_message:
    #         encouragement_message = encouragement_message.replace("{childName}", child_name)
    #         encouragement_message = encouragement_message.replace("{文杰}", child_name)
        
    #     # 根据成功条件进行匹配
    #     if success_condition == "exact":
    #         # 完全匹配：用户输入与期望短语一模一样
    #         is_passed = user_text in expected_phrases
    #         score = 100 if is_passed else 0
    #         if is_passed and praise_message:
    #             feedback = praise_message
    #         else:
    #             feedback = "回答完全正确！" if is_passed else (encouragement_message if encouragement_message else "请完全按照要求回答。")
            
    #     elif success_condition == "partial":
    #         # 部分匹配：用户输入包含在期望短语内，或者包含期望关键词
    #         is_passed = False
    #         score = 0
            
    #         # 首先检查期望短语
    #         if expected_phrases:
    #             for phrase in expected_phrases:
    #                 if phrase in user_text or user_text in phrase:
    #                     is_passed = True
    #                     score = 80
    #                     break
            
    #         # 如果期望短语为空或没有匹配，检查期望关键词
    #         if not is_passed and expected_keywords:
    #             for keyword in expected_keywords:
    #                 if keyword in user_text:
    #                     is_passed = True
    #                     score = 70
    #                     break
            
    #         if is_passed and praise_message:
    #             feedback = praise_message
    #         else:
    #             feedback = "回答正确！" if is_passed else (encouragement_message if encouragement_message else "请尝试更完整的回答。")
            
    #     elif success_condition == "keyword":
    #         # 关键词匹配：用户输入包含期望关键词中的任何一个
    #         is_passed = False
    #         score = 0
            
    #         if expected_keywords:
    #             for keyword in expected_keywords:
    #                 if keyword in user_text:
    #                     is_passed = True
    #                     score = 60
    #                     break
            
    #         if is_passed and praise_message:
    #             feedback = praise_message
    #         else:
    #             feedback = "包含关键词，回答正确！" if is_passed else (encouragement_message if encouragement_message else "请使用相关的关键词回答。")
            
    #     else:
    #         # 默认使用关键词匹配
    #         is_passed = False
    #         score = 0
            
    #         if expected_keywords:
    #             for keyword in expected_keywords:
    #                 if keyword in user_text:
    #                     is_passed = True
    #                     score = 60
    #                     break
            
    #         if is_passed and praise_message:
    #             feedback = praise_message
    #         else:
    #             feedback = "包含关键词，回答正确！" if is_passed else (encouragement_message if encouragement_message else "请使用相关的关键词回答。")
        
    #     self.logger.info(f"匹配结果: is_passed={is_passed}, score={score}")
        
    #     # 生成评估结果
    #     result = {
    #         "score": score,
    #         "is_passed": is_passed,
    #         "feedback": feedback,
    #         "retry_count": retry_count,
    #         "success_condition": success_condition,
    #         "user_input": user_text,
    #         "expected_keywords": expected_keywords,
    #         "expected_phrases": expected_phrases
    #     }
        
    #     self.logger.info(f"评估结果: {result}")
    #     return result

    def _evaluate_response_with_config(self, step_config: Dict, user_text: str, session_data: Dict) -> Dict:
        """根据步骤配置评估用户回复 - 简化匹配逻辑"""
        self.logger.info(f"=== 根据步骤配置评估用户回复 ===")
        self.logger.info(f"步骤配置: {step_config}")
        self.logger.info(f"用户输入: {user_text}")
        
        # 获取配置参数
        success_condition = step_config.get("successCondition", "")  # 保留原有，但实际不直接使用
        print("--------------------------------success_condition--------------------------------", success_condition)
        
        expected_keywords_str = step_config.get("expectedKeywords", "")
        expected_phrases_str = step_config.get("expectedPhrases", "")
        max_attempts = step_config.get("maxAttempts", 3)
        retry_count = session_data.get("retry_count", 0)
        
        self.logger.info(f"成功条件: {success_condition}")
        self.logger.info(f"期望关键词: {expected_keywords_str}")
        self.logger.info(f"期望短语: {expected_phrases_str}")
        self.logger.info(f"最大尝试次数: {max_attempts}")
        self.logger.info(f"当前重试次数: {retry_count}")
        
        # 解析期望关键词和短语
        expected_keywords = self._parse_json_list(expected_keywords_str)
        expected_phrases = self._parse_json_list(expected_phrases_str)
        
        self.logger.info(f"解析后的期望关键词: {expected_keywords}")
        self.logger.info(f"解析后的期望短语: {expected_phrases}")
        
        # 获取配置中的鼓励话语
        praise_message = step_config.get("praiseMessage", "")
        encouragement_message = step_config.get("encouragementMessage", "")
        
        # 替换儿童姓名占位符
        child_name = session_data.get("child_name", "小朋友")
        if praise_message:
            praise_message = praise_message.replace("{childName}", child_name)
            praise_message = praise_message.replace("{文杰}", child_name)
        if encouragement_message:
            encouragement_message = encouragement_message.replace("{childName}", child_name)
            encouragement_message = encouragement_message.replace("{文杰}", child_name)
        
        # 简化匹配逻辑：统一计算匹配类型和分数
        from difflib import SequenceMatcher  # 引入标准库用于相似度计算
        
        user_text_clean = user_text.strip().lower()
        score = 0
        is_passed = False
        match_type = "no_match"  # 默认：完全不匹配
        feedback = encouragement_message or "请尝试更完整的回答。"
        
        # 1. 先匹配期望短语：计算最大相似度，如果 >=80%，为完全匹配
        max_similarity = 0
        if expected_phrases:
            for phrase in expected_phrases:
                phrase_clean = phrase.strip().lower()
                similarity = SequenceMatcher(None, user_text_clean, phrase_clean).ratio() * 100
                if similarity > max_similarity:
                    max_similarity = similarity
                self.logger.info(f"短语 '{phrase_clean}' 与用户输入相似度: {similarity:.2f}%")
        
        if max_similarity >= 80:
            score = 100
            is_passed = True
            match_type = "exact"  # 完全匹配
            feedback = praise_message or "回答完全正确！"
            self.logger.info(f"完全匹配：最大相似度 {max_similarity:.2f}% >= 80%")
        else:
            self.logger.info(f"短语相似度不足：最大 {max_similarity:.2f}% < 80%，进入关键词匹配")
            
            # 2. 低于80%时，匹配期望关键词：如果任何一个关键词在用户输入中，为部分匹配
            if expected_keywords:
                for keyword in expected_keywords:
                    keyword_clean = keyword.strip().lower()
                    if keyword_clean in user_text_clean:
                        score = 70  # 部分匹配分数
                        is_passed = True
                        match_type = "partial"
                        feedback = praise_message or "回答正确！"
                        self.logger.info(f"部分匹配：包含关键词 '{keyword_clean}'")
                        break  # 命中一个即可
            
            if match_type == "partial":
                self.logger.info("确认部分匹配")
            else:
                # 3. 否则，完全不匹配
                score = 0
                match_type = "no_match"
                feedback = encouragement_message or "请使用相关的关键词回答。"
                self.logger.info("完全不匹配")
        
        self.logger.info(f"匹配结果: match_type={match_type}, score={score}, is_passed={is_passed}")
        
        # 生成评估结果（基于实际匹配得出 success_condition 取值）
        result = {
            "score": score,
            "is_passed": is_passed,
            "feedback": feedback,
            "retry_count": retry_count,
            "success_condition": match_type,  # exact / partial / no_match
            "user_input": user_text,
            "expected_keywords": expected_keywords,
            "expected_phrases": expected_phrases,
            "max_phrase_similarity": max_similarity  # 新增：记录最大相似度，便于调试
        }
        
        self.logger.info(f"评估结果: {result}")
        return result



    def _parse_json_list(self, json_str: str) -> List[str]:
        """解析JSON格式的字符串列表
        
        Args:
            json_str: JSON格式的字符串
            
        Returns:
            List[str]: 解析后的字符串列表
        """
        if not json_str:
            return []
        
        try:
            # 尝试JSON解析
            result = json.loads(json_str)
            if isinstance(result, list):
                return [str(item).strip() for item in result if item]
            else:
                return [str(result).strip()]
        except (json.JSONDecodeError, TypeError):
            # 如果JSON解析失败，尝试按逗号分割
            return [item.strip() for item in json_str.split(",") if item.strip()]



    
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
    
    def _calculate_final_score(self, session_data: Dict) -> int:
        """计算最终分数
        
        Args:
            session_data: 会话数据
            
        Returns:
            int: 最终分数
        """
        evaluations = session_data.get("evaluations", [])
        if not evaluations:
            return 0
        
        total_score = sum(eval.get("score", 0) for eval in evaluations)
        final_score = int(total_score / len(evaluations))
        
        self.logger.info(f"计算最终分数: {total_score}/{len(evaluations)} = {final_score}")
        return final_score

    async def check_teaching_timeout(self, user_id: str) -> Optional[Dict[str, Any]]:
        """检查教学会话是否超时 - 优化版本，支持渐进式提示和步骤跳转
        
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
        
        wait_start_time = session_data.get("wait_start_time")
        if wait_start_time is None:
            self.logger.info(f"等待开始时间未设置，跳过超时检查")
            return None
            
        current_time = time.time()
        wait_duration = current_time - wait_start_time
        
        # 获取当前步骤的超时时间
        scenario_id = session_data.get("scenario_id")
        current_step_index = session_data.get("current_step", 0)
        
        # 获取当前步骤配置
        steps = await self.dialogue_service._get_scenario_steps(scenario_id)
        if steps and current_step_index < len(steps):
            current_step = steps[current_step_index]
            timeout_seconds = current_step.get("timeoutSeconds", self.WAIT_TIME_MAX)
        else:
            timeout_seconds = self.WAIT_TIME_MAX
        
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
                warning_message = warning_message.replace("{childName}", child_name)
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
                final_message = final_message.replace("{childName}", child_name)
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
            
            # 获取当前步骤的超时处理配置
            if steps and current_step_index < len(steps):
                current_step = steps[current_step_index]
                self.logger.info(f"当前步骤数据: {current_step}")
                
                # 使用auto_reply_on_timeout作为超时消息
                auto_reply = current_step.get("autoReplyOnTimeout")
                
                self.logger.info(f"自动回复消息: {auto_reply}")
                self.logger.info(f"超时后直接走成功条件分支配置")
                
                # 优化超时消息，增加鼓励性
                if auto_reply:
                    timeout_message = auto_reply
                else:
                    timeout_message = "时间到了，让我们继续学习下一个内容。"
                
                # 替换儿童姓名占位符
                child_name = session_data.get("child_name", "小朋友")
                if timeout_message:
                    timeout_message = timeout_message.replace("{childName}", child_name)
                    timeout_message = timeout_message.replace("{文杰}", child_name)
            else:
                self.logger.warning(f"无法获取步骤数据，使用默认超时消息")
                timeout_message = "时间到了，让我们继续学习下一个内容。"
            
            self.logger.info(f"最终超时消息: {timeout_message}")
            
            # 更新会话状态 - 超时后进入下一步
            session_data["waiting_for_response"] = False
            session_data["warning_sent"] = False
            session_data["final_reminder_sent"] = False
            
            # 检查是否需要进入下一步
            if steps and current_step_index < len(steps):
                # 获取当前步骤的最大尝试次数（优先步骤配置，备用场景配置）
                step_max_attempts = self._get_step_max_attempts(current_step, session_data)
                current_step_retry_count = session_data.get("current_step_retry_count", 0)
                
                # 判断是否为叶子节点
                is_leaf_step = self._is_leaf_step(current_step)
                
                self.logger.info(f"超时检查 - 步骤最大尝试次数: {step_max_attempts}")
                self.logger.info(f"超时检查 - 当前步骤重试次数: {current_step_retry_count}")
                self.logger.info(f"超时检查 - 是否为叶子节点: {is_leaf_step}")
                
                if is_leaf_step:
                    # 叶子节点：检查步骤级别的重试次数
                    if current_step_retry_count >= step_max_attempts:
                        # 叶子节点超过最大尝试次数，结束教学
                        self.logger.warning(f"叶子节点超时且超过最大尝试次数，结束教学")
                        final_score = self._calculate_final_score(session_data)
                        session_data["completed"] = True
                        session_data["final_score"] = final_score
                        session_data["completion_reason"] = "timeout_leaf_step_max_attempts_exceeded"
                        
                        # 保存会话数据
                        self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                        
                        # 生成完成消息
                        completion_message = self._generate_completion_message(final_score, child_name)
                        
                        return {
                            "success": True,
                            "action": "completed",
                            "ai_message": completion_message,
                            "final_score": final_score,
                            "message": f"教学完成！最终得分：{final_score}分"
                        }
                    else:
                        # 叶子节点未超过最大尝试次数，增加重试次数并继续当前步骤
                        session_data["current_step_retry_count"] = current_step_retry_count + 1
                        self.logger.info(f"叶子节点超时但未超过最大尝试次数，增加重试次数: {session_data['current_step_retry_count']}/{step_max_attempts}")
                        
                        # 保存会话数据
                        self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                        
                        return {
                            "success": True,
                            "action": "retry_current_step",
                            "message": "超时后重试当前步骤",
                            "timeoutSeconds": current_step.get("timeoutSeconds", self.WAIT_TIME_MAX),
                            "retry_count": session_data["current_step_retry_count"],
                            "max_attempts": step_max_attempts,
                            "is_leaf_step": True
                        }
                else:
                    # 非叶子节点：使用原有的分支配置逻辑
                    if current_step_retry_count >= step_max_attempts:
                        # 超过最大尝试次数，使用完全不匹配分支配置进入下一步
                        next_step_id = current_step.get("noMatchNextStepId") or current_step.get("noMatchStepId")
                        if next_step_id:
                            self.logger.info(f"超时且超过最大尝试次数，使用noMatchStepId跳转: {next_step_id}")
                            # 查找指定的下一步骤
                            next_step_index = self._find_step_by_id(steps, next_step_id)
                            if next_step_index is not None:
                                session_data["current_step"] = next_step_index
                                session_data["current_step_retry_count"] = 0  # 重置新步骤的重试次数
                                self.logger.info(f"超时后跳转到指定步骤: {next_step_index}")
                            else:
                                self.logger.warning(f"超时后未找到指定的下一步骤ID: {next_step_id}，教学结束")
                                # 如果找不到指定的步骤，结束教学
                                final_score = self._calculate_final_score(session_data)
                                session_data["completed"] = True
                                session_data["final_score"] = final_score
                                session_data["completion_reason"] = "timeout_branch_step_not_found"
                                
                                # 保存会话数据
                                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                                
                                # 生成完成消息
                                completion_message = self._generate_completion_message(final_score, child_name)
                                
                                return {
                                    "success": True,
                                    "action": "completed",
                                    "ai_message": completion_message,
                                    "final_score": final_score,
                                    "message": f"教学完成！最终得分：{final_score}分"
                                }
                        else:
                            # 没有配置noMatchStepId，结束教学
                            self.logger.warning(f"超时且没有配置noMatchStepId，教学结束")
                            final_score = self._calculate_final_score(session_data)
                            session_data["completed"] = True
                            session_data["final_score"] = final_score
                            session_data["completion_reason"] = "timeout_no_branch_config"
                            
                            # 保存会话数据
                            self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                            
                            # 生成完成消息
                            completion_message = self._generate_completion_message(final_score, child_name)
                            
                            return {
                                "success": True,
                                "action": "completed",
                                "ai_message": completion_message,
                                "final_score": final_score,
                                "message": f"教学完成！最终得分：{final_score}分"
                            }
                    
                        # 重置当前步骤重试次数（进入新步骤时重置）
                        session_data["current_step_retry_count"] = 0
                        self.logger.info(f"超时且超过最大尝试次数，进入下一步: {session_data['current_step']}")
                        
                        # 检查是否完成所有步骤
                        if session_data["current_step"] >= len(steps):
                            self.logger.info(f"已完成所有步骤，教学结束")
                            # 教学完成
                            final_score = self._calculate_final_score(session_data)
                            session_data["completed"] = True
                            session_data["final_score"] = final_score
                            
                            # 保存会话数据
                            self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                            
                            # 生成完成消息
                            completion_message = self._generate_completion_message(final_score, child_name)
                            
                            return {
                                "success": True,
                                "action": "completed",
                                "ai_message": completion_message,
                                "final_score": final_score,
                                "message": f"教学完成！最终得分：{final_score}分"
                            }
                        else:
                            # 进入下一步
                            next_step = steps[session_data["current_step"]]
                            
                            # 保存会话数据
                            self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                            
                            return {
                                "success": True,
                                "action": "next_step",
                                "timeoutSeconds": next_step.get("timeoutSeconds", self.WAIT_TIME_MAX),
                                "message": "超时后进入下一步"
                            }
                    else:
                        # 非叶子节点未超过最大尝试次数，增加重试次数并继续当前步骤
                        session_data["current_step_retry_count"] = current_step_retry_count + 1
                        self.logger.info(f"非叶子节点超时但未超过最大尝试次数，增加重试次数: {session_data['current_step_retry_count']}/{step_max_attempts}")
                        
                        # 保存会话数据
                        self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                        
                        return {
                            "success": True,
                            "action": "retry_current_step",
                            "message": "超时后重试当前步骤",
                            "timeoutSeconds": current_step.get("timeoutSeconds", self.WAIT_TIME_MAX),
                            "retry_count": session_data["current_step_retry_count"],
                            "max_attempts": step_max_attempts,
                            "is_leaf_step": False
                        }
            
            result = {
                "success": True,
                "action": "timeout_response",
                "message": "用户超时，进入下一步"
            }
            self.logger.info(f"返回超时处理结果: {result}")
            return result
        else:
            self.logger.info(f"未超时，等待时长: {wait_duration}秒 < {timeout_seconds}秒")
        
        return None
    
    def _find_step_by_id(self, steps: List[Dict], step_id: str) -> Optional[int]:
        """根据步骤ID查找步骤索引
        
        Args:
            steps: 步骤列表
            step_id: 要查找的步骤ID
            
        Returns:
            int: 步骤索引，如果未找到返回None
        """
        # 首先记录所有步骤的ID信息用于调试
        self.logger.info(f"查找步骤ID: {step_id}")
        self.logger.info("当前所有步骤的ID信息:")
        for i, step in enumerate(steps):
            self.logger.info(f"  步骤{i}: id={step.get('id')}, stepId={step.get('stepId')}, stepCode={step.get('stepCode')}")
        
        # 尝试多种ID字段匹配
        for i, step in enumerate(steps):
            # 匹配 stepId 字段
            if step.get("stepId") == step_id:
                self.logger.info(f"通过stepId找到步骤ID {step_id}，索引为 {i}")
                return i
            # 匹配 id 字段
            if step.get("id") == step_id:
                self.logger.info(f"通过id字段找到步骤ID {step_id}，索引为 {i}")
                return i
            # 匹配 stepCode 字段
            if step.get("stepCode") == step_id:
                self.logger.info(f"通过stepCode找到步骤ID {step_id}，索引为 {i}")
                return i
        
        self.logger.warning(f"未找到步骤ID: {step_id}")
        return None

    def _get_step_max_attempts(self, step_config: Dict, session_data: Dict) -> int:
        """获取步骤的最大尝试次数，优先使用步骤配置，如果没有则使用场景配置
        
        Args:
            step_config: 步骤配置
            session_data: 会话数据
            
        Returns:
            int: 最大尝试次数
        """
        # 优先使用步骤配置的maxAttempts
        step_max_attempts = step_config.get("maxAttempts")
        if step_max_attempts is not None and step_max_attempts > 0:
            self.logger.info(f"使用步骤配置的最大尝试次数: {step_max_attempts}")
            return step_max_attempts
        
        # 如果步骤没有配置，使用场景配置的maxUserReplies
        scenario_max_replies = session_data.get("max_user_replies", 3)
        self.logger.info(f"步骤未配置maxAttempts，使用场景配置的最大回复次数: {scenario_max_replies}")
        return scenario_max_replies
    
    def _is_leaf_step(self, step_config: Dict) -> bool:
        """判断是否为叶子节点（没有配置成功条件分支配置）
        
        Args:
            step_config: 步骤配置
            
        Returns:
            bool: 是否为叶子节点
        """
        # 检查是否有任何分支配置
        has_branch_config = (
            step_config.get("perfectMatchNextStepId") or 
            step_config.get("exactMatchStepId") or
            step_config.get("partialMatchNextStepId") or 
            step_config.get("partialMatchStepId") or
            step_config.get("noMatchNextStepId") or 
            step_config.get("noMatchStepId")
        )
        
        is_leaf = not has_branch_config
        self.logger.info(f"步骤是否为叶子节点: {is_leaf} (有分支配置: {has_branch_config})")
        return is_leaf
    
    def _get_random_message(self, messages: List[str]) -> str:
        """从消息列表中随机选择一条消息
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 随机选择的消息
        """
        import random
        return random.choice(messages) if messages else "加油！"
