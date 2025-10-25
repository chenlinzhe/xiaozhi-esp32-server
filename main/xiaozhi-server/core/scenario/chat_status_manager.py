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
            # self.logger.info(f"开始教学会话: user_id={user_id}, child_name={child_name}, from_mode_switch={from_mode_switch}")
            
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
                # print(f"获取到的所有场景: {scenarios}")
                # self.logger.info(f"获取到 {len(scenarios) if scenarios else 0} 个场景")
                
                if not scenarios or len(scenarios) == 0:
                    self.logger.error("没有可用的教学场景")
                    return {
                        "success": False,
                        "error": "没有可用的教学场景，请联系管理员配置教学场景"
                    }
                default_scenario = scenarios[0]
                # print(f"选择第一个场景详情:")
                # print(f"  - 场景ID: {default_scenario.get('id', 'N/A')}")
                # print(f"  - 场景名称: {default_scenario.get('scenarioName', 'N/A')}")
                # print(f"  - 是否活跃: {default_scenario.get('isActive', 'N/A')}")
                # print(f"  - 代理ID: {default_scenario.get('agentId', 'N/A')}")
                # print(f"  - 是否默认教学: {default_scenario.get('isDefaultTeaching', 'N/A')}")
                # print(f"  - 创建时间: {default_scenario.get('createTime', 'N/A')}")
                # print(f"  - 更新时间: {default_scenario.get('updateTime', 'N/A')}")
                # print(f"  - 完整第一个场景数据: {default_scenario}")
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
                    # "step_retry_counts": {},  # 每个步骤的重试计数 {step_index: retry_count}
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
                
                # self.logger.info(f"教学会话开始成功: {response}")
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
            # self.logger.info(f"当前步骤详情: {current_step}")
            
            # 智能评估用户回复
            self.logger.info(f"=== 开始智能评估 ===")
            self.logger.info(f"评估输入: user_text={user_text}")
            # self.logger.info(f"评估会话: {full_session}")
            
            evaluation = self._evaluate_response_with_config(current_step, user_text, session_data)
            score = evaluation["score"]
            
            # self.logger.info(f"评估结果: {evaluation}")
            self.logger.info(f"评估分数: {score}")
            # self.logger.info(f"是否通过: {evaluation.get('is_passed', False)}")
            
            # 记录评估结果
            session_data["evaluations"].append(evaluation)
            self.logger.info(f"已记录评估结果到会话数据")
            
            # 更新用户回复次数统计
            session_data["total_user_replies"] = session_data.get("total_user_replies", 0) + 1
            current_replies = session_data["total_user_replies"]
            
            # 获取当前步骤的最大尝试次数（优先步骤配置，备用场景配置）
            step_max_attempts = self._get_step_max_attempts(current_step, session_data)
            current_step_retry_count = session_data.get("current_step_retry_count", 0)
            
            self.logger.info(f"步骤最大尝试次数: {step_max_attempts}")
            self.logger.info(f"当前步骤已学习次数: {current_step_retry_count+1}次")
            self.logger.info(f"用户总回复次数: {current_replies}")
            
            # 简化逻辑：所有步骤都按叶子节点处理，重复输出AI消息列表
            self.logger.info(f"处理步骤逻辑 - 重复输出AI消息列表")
            
            # 增加当前步骤重试次数
            session_data["current_step_retry_count"] = current_step_retry_count + 1
            self.logger.info(f"增加重试次数: {session_data['current_step_retry_count']}/{step_max_attempts}")
            
            # 检查是否超过最大尝试次数
            if session_data["current_step_retry_count"] >= step_max_attempts:
                self.logger.warning(f"超过最大尝试次数，结束教学")
                final_score = self._calculate_final_score(session_data)
                session_data["completed"] = True
                session_data["final_score"] = final_score
                session_data["completion_reason"] = "max_attempts_exceeded"
                
                # 保存会话数据
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                
                # 切换到自由模式
                self.set_user_chat_status(user_id, "free_mode")

                # 立即清理教学会话数据
                self.redis_client.delete_session_data(f"teaching_{user_id}")
                self.logger.info(f"已清理教学会话数据: teaching_{user_id}")

                # 获取当前步骤的鼓励词
                encouragement_words = current_step.get('encouragementWords', '')
                self.logger.info(f"当前步骤鼓励词: {encouragement_words}")

                return {
                    "success": True,
                    "action": "completed",
                    "reason": "max_attempts_exceeded",
                    "ai_message": f"你真棒！你已经学习了{current_step_retry_count + 1}次，出色地完成了学习任务。教学结束，最终得分：{final_score}分。",
                    "final_score": final_score,
                    "total_attempts": current_step_retry_count + 1,
                    "max_attempts": step_max_attempts,
                    "encouragement_words": encouragement_words
                }
            else:
                # 未超过最大尝试次数，重复输出AI消息列表
                self.logger.info(f"重复输出AI消息列表，重试次数: {session_data['current_step_retry_count']}/{step_max_attempts}")
                
                # 获取步骤的消息列表
                step_id = current_step.get("stepId")
                message_list = None
                if step_id:
                    message_list = self._get_step_message_list(step_id)
                    self.logger.info(f"获取到步骤 {step_id} 的消息列表: {len(message_list) if message_list else 0} 条消息")
                
                # 设置等待响应状态
                session_data["waiting_for_response"] = True
                session_data["wait_start_time"] = time.time()
                session_data["warning_sent"] = False
                session_data["final_reminder_sent"] = False
                
                # 保存会话数据
                self.redis_client.set_session_data(f"teaching_{user_id}", session_data)
                
                # 构建返回结果
                result = {
                    "success": True,
                    "action": "retry_current_step",
                    "session_id": f"teaching_{user_id}",
                    "current_step": current_step,
                    "evaluation": evaluation,
                    "message": f"让我们再试一次：{evaluation['feedback']}",
                    "timeoutSeconds": current_step.get("timeoutSeconds", self.WAIT_TIME_MAX),
                    "retry_count": session_data["current_step_retry_count"],
                    "max_attempts": step_max_attempts
                }
                
                # 如果有消息列表，添加到返回结果中
                if message_list:
                    result["message_list"] = message_list
                    result["message_count"] = len(message_list)
                    self.logger.info(f"返回消息列表，消息数量: {len(message_list)}")
                
                return result
                    
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


    def _evaluate_response_with_config(self, step_config: Dict, user_text: str, session_data: Dict) -> Dict:
        """根据步骤配置评估用户回复 - 简化匹配逻辑"""
        self.logger.info(f"=== 根据步骤配置评估用户回复 ===")
        # self.logger.info(f"步骤配置: {step_config}")
        self.logger.info(f"用户输入: {user_text}")
        
        # 获取配置参数
        success_condition = ""  # 保留原有，但实际不直接使用
        print("--------------------------------success_condition--------------------------------", success_condition)
        
        expected_keywords_str = step_config.get("expectedKeywords", "")
        expected_phrases_str = step_config.get("expectedPhrases", "")
        max_attempts = step_config.get("maxAttempts", 3)
        
        self.logger.info(f"成功条件: {success_condition}")
        self.logger.info(f"期望关键词: {expected_keywords_str}")
        self.logger.info(f"期望短语: {expected_phrases_str}")
        self.logger.info(f"最大尝试次数: {max_attempts}")
        
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
            # "retry_count": retry_count,
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

    # 
    

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
    
    
    def _get_step_message_list(self, step_id: str) -> Optional[List[Dict]]:
        """获取步骤的消息列表
        
        Args:
            step_id: 步骤ID
            
        Returns:
            List[Dict]: 消息列表，如果获取失败返回None
        """
        try:
            self.logger.info(f"获取步骤消息列表，步骤ID: {step_id}")
            
            # 导入API客户端
            from config.manage_api_client import get_step_messages
            
            message_list = get_step_messages(step_id)
            # self.logger.info(f"API返回结果: {message_list}")
            
            if message_list and len(message_list) > 0:
                self.logger.info(f"获取到消息列表，消息数量: {len(message_list)}")
                return message_list
            else:
                self.logger.info(f"步骤 {step_id} 没有配置消息列表或返回空结果")
                return None
                
        except Exception as e:
            self.logger.error(f"获取步骤消息列表失败: {e}")
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
