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
from typing import Dict
from difflib import SequenceMatcher
from xpinyin import Pinyin  # 必须导入


class ChatState(Enum):
    """聊天状态枚举 - 基于思维导图设计"""
    FREE_CHAT = "free_chat"  # 自由聊天模式
    TEACHING_MODE = "teaching_mode"  # 教学模式
    WAITING_RESPONSE = "waiting_response"  # 等待用户响应
    EVALUATING = "evaluating"  # 评估用户回复
    COMPLETED = "completed"  # 教学完成


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

        # 新增：初始化拼音转换器（只创建一次）
        self.pinyin = Pinyin()




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

    async def _start_teaching_session(self, user_id: str, child_name: str, from_mode_switch: bool = False) -> Dict[
        str, Any]:
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


            print("in _start_teaching_session------------------------------------------------------")
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
                    "evaluations": [],  # 新增评估结果列表
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
            self.logger.info(f"场景ID: {scenario_id}, 当前步骤: {current_step_index+1}")

            # 获取场景步骤
            self.logger.info(f"正在获取场景步骤: scenario_id={scenario_id}")
            steps = await self.dialogue_service._get_scenario_steps(scenario_id)
            self.logger.info(f"获取到 {len(steps) if steps else 0} 个场景步骤")

            if not steps or current_step_index >= len(steps):
                self.logger.error(
                    f"场景步骤配置错误: steps={len(steps) if steps else 0}, current_step_index={current_step_index}")
                return {
                    "success": False,
                    "error": "场景步骤配置错误"
                }

            # 构建完整的session数据供评估使用
            # 🔥 更新session_data中的child_name，确保后续步骤使用正确的姓名
            session_data["child_name"] = child_name

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

            # 判断是否为叶子节点
            is_leaf_step = self._is_leaf_step(current_step)

            self.logger.info(f"步骤最大尝试次数: {step_max_attempts}")
            self.logger.info(f"当前步骤已学习次数: {current_step_retry_count + 1}次")
            self.logger.info(f"是否为叶子节点: {is_leaf_step}")
            self.logger.info(f"用户总回复次数: {current_replies}")
            self.logger.info(f"当前步骤: {current_step_index+1}")

            # 提前提取鼓励词
            encouragement_words = ''
            encouragement_words = steps[current_step_index].get('encouragementWords', '') or ''

            last_encouragement_words = ''
            if len(steps) - 1 >= 0:
                last_encouragement_words = steps[len(steps) - 1].get('encouragementWords', '') or ''

            self.logger.info(f"当前步骤鼓励词: {encouragement_words}")
            self.logger.info(f"最后步骤鼓励词: {last_encouragement_words}")

            # 根据评估结果决定下一步 - 区分叶子节点和非叶子节点
            self.logger.info(f"=== 根据评估结果决定下一步 ===")
            self.logger.info(f"评估分数: {score}")
            self.logger.info(f"是否通过: {evaluation.get('is_passed', False)}")
            self.logger.info(f"是否为叶子节点: {is_leaf_step}")

            
            # 叶子节点处理：不管用户回复什么，都重复输出AI消息列表
            # 叶子节点的，会返回结果，给前端；
            if is_leaf_step:
                
                self.logger.info(f"处理叶子节点逻辑 - 重复输出AI消息列表")

                # 计入当前步骤已重试次数
                session_data["current_step_retry_count"] = current_step_retry_count + 1
                self.logger.info(
                    f"在叶子节点、计入已重试次数: {session_data['current_step_retry_count']}/{step_max_attempts}")

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

                    # ⚠️ 新增：立即清理教学会话数据
                    self.redis_client.delete_session_data(f"teaching_{user_id}")
                    self.logger.info(f"已清理教学会话数据: teaching_{user_id}")

                    return {
                        "success": True,
                        "action": "completed",
                        "reason": "leaf_step_max_attempts_exceeded",
                        "ai_message": f"{encouragement_words}，{child_name}小朋友你真棒！你已经学习了{session_data['current_step_retry_count']}次，出色地完成了学习任务,送你一朵小红花!教学结束",
                        "final_score": final_score,
                        "total_attempts": session_data["current_step_retry_count"],
                        "max_attempts": step_max_attempts
                    }
                
                
                # 叶子节点未超过最大尝试次数，还在循环中，每次输出一组AI消息列表
                else:
                    
                    self.logger.info(
                        f"叶子节点重复输出AI消息列表，重试次数: {session_data['current_step_retry_count']}/{step_max_attempts}")

                    # 获取步骤的消息列
                    step_id = current_step.get("stepId")
                    message_list = None
                    if step_id:
                        message_list = self._get_step_message_list(step_id)
                        self.logger.info(
                            f"获取到步骤 {step_id} 的消息列表: {len(message_list) if message_list else 0} 条消息")

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
                        "ai_message": f"{encouragement_words},{evaluation['feedback']},让我们再试一次：",
                        "timeoutSeconds": current_step.get("timeoutSeconds", self.WAIT_TIME_MAX),
                        "retry_count": session_data["current_step_retry_count"],
                        "max_attempts": step_max_attempts,
                        "is_leaf_step": True
                    }

                    # 如果有消息列表，添加到返回结果中
                    if message_list:
                        result["message_list"] = message_list
                        result["message_count"] = len(message_list)
                        self.logger.info(f"叶子节点返回消息列表，消息数量: {len(message_list)}")

                    return result
            
            
            # 非叶子节点处理：使用分支配置，这里不会返回，是继续走流程；
            else:
                
                self.logger.info(f"处理非叶子节点逻辑，设置branch和next_step_id")

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

            # 继续走流程（非叶子结点的)，根据分支配置决定跳转
            # 如果非叶子结点，有分支的

            if next_step_id:
                self.logger.info(f"非叶子结点的，有分支的，根据{branch_type}分支配置，跳转到步骤ID: {next_step_id}")
                # 查找指定的下一步骤
                next_step_index = self._find_step_by_id(steps, next_step_id)
                if next_step_index is not None:
                    session_data["current_step"] = next_step_index
                    self.logger.info(f"跳转到指定步骤: {next_step_index+1}")
                else:
                    # 如果找不到指定的步骤，尝试回退到下一个步骤
                    current_step_index = session_data.get("current_step", 0)
                    next_step_index = current_step_index + 1

                    if next_step_index < len(steps):
                        self.logger.warning(
                            f"未找到指定的下一步骤ID: {next_step_id}，回退到下一个步骤: {next_step_index}")
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
                            "ai_message": f"教学完成，你真棒，下次我们再继续！",
                            "final_score": final_score
                        }

            # 如果非叶子结点，没有分支的，直接结束教学
            else:
                
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
                    "ai_message": f"教学完成，你真棒，下次我们再继续！",
                    "final_score": final_score
                }



            # 执行场景: 非叶子节点，有有效的 next_step_id，找到了步骤，
            # 且未到达所有步骤末尾（e.g., 正常步骤跳转时）。


            # 设置等待响应状态
            session_data["waiting_for_response"] = True
            session_data["wait_start_time"] = time.time()
            session_data["warning_sent"] = False
            session_data["final_reminder_sent"] = False
            self.logger.info(f"更新步骤: {session_data['current_step']+1}")
            self.logger.info(
                f"设置等待响应状态: waiting_for_response=True, wait_start_time={session_data['wait_start_time']}")


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

                # 🔥 切换到自由模式
                self.set_user_chat_status(user_id, "free_mode")
                self.logger.info(f"✅ 已切换用户 {user_id} 到自由模式")

                # 获取最后一个步骤的鼓励词
                last_step_index = session_data["current_step"] - 1
                encouragement_words = ''
                if last_step_index >= 0 and last_step_index < len(steps):
                    last_step = steps[last_step_index]
                    encouragement_words = last_step.get('encouragementWords', '')
                    self.logger.info(f"------------------最后步骤鼓励词: {encouragement_words}")

                # 生成完成消息
                completion_message = self._generate_completion_message(final_score, child_name)
                if last_encouragement_words:
                    completion_message = f"{last_encouragement_words} {completion_message}"
                self.logger.info(f"生成完成消息: {completion_message}")

                result = {
                    "success": True,
                    "action": "completed",
                    "session_id": f"teaching_{user_id}",
                    "ai_message": completion_message,
                    "final_score": final_score,
                    "evaluation": evaluation,
                    "message": f"教学完成，你真棒，下次我们再继续！",
                    "encouragement_words": last_encouragement_words
                }
                self.logger.info(f"返回完成结果: {result}")
                return result

            # 非叶子节点、未完成所有步骤
            else:
                self.logger.info(f"进入下一步，步骤: {session_data['current_step']+1}")

                # 获取当前步骤的鼓励词（在进入下一步前）
                # current_step_index = session_data["current_step"] - 1  # 当前步骤索引

                # print("current_step_index======非叶子节点、未完成所有步骤=============",current_step_index)

                # if current_step_index >= 0 and current_step_index < len(steps):
                #     current_step = steps[current_step_index]
                #     encouragement_words = current_step.get('encouragementWords', '')


                #     self.logger.info(f"-----------非叶子节点、未完成所有步骤--------当前步骤鼓励词: {encouragement_words}")
                # else:
                #     encouragement_words = '在最后一步的鼓励词  非叶子节点、未完成所有步骤'

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

                # 根据分支类型确定action
                if branch_type == "perfect_match":
                    action = "perfect_match_next"
                elif branch_type == "partial_match":
                    action = "partial_match_next"
                elif branch_type == "no_match":
                    action = "no_match_next"
                else:
                    action = "next_step"

                feedback_message = evaluation['feedback']
                if encouragement_words:
                    feedback_message = f"{encouragement_words} {feedback_message}"

                result = {
                    "success": True,
                    "action": action,
                    "session_id": f"teaching_{user_id}",
                    "current_step": next_step,
                    "evaluation": evaluation,
                    "ai_message": f"{feedback_message}",
                    "timeoutSeconds": timeout_seconds,
                    "total_replies": current_replies,

                    "max_replies": session_data.get("max_user_replies", 3),
                    # "reply_progress": reply_progress,
                    # "warning_message": warning_message,
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
                    self.logger.warning(
                        f"异常情况下仍记录回复次数 - 用户: {user_id}, 总回复次数: {session_data.get('total_user_replies', 0)}")
            except Exception as log_error:
                self.logger.error(f"记录异常回复次数失败: {str(log_error)}")

            return {
                "success": False,
                "error": f"处理教学回复失败: {str(e)}",
                "total_replies": session_data.get("total_user_replies", 0) if 'session_data' in locals() else 0
            }













    def _evaluate_response_with_config(self, step_config: Dict, user_text: str, session_data: Dict) -> Dict:
        """根据步骤配置评估用户回复 - 短语包含即完全匹配（含拼音）"""
        self.logger.info(f"=== 根据步骤配置评估用户回复 ===")
        self.logger.info(f"用户输入: {user_text}")

        # 获取配置参数
        success_condition = ""  # 保留原有
        print("--------------------------------success_condition--------------------------------", success_condition)

        expected_keywords_str = step_config.get("expectedKeywords", "")
        expected_phrases_str = step_config.get("expectedPhrases", "")
        max_attempts = step_config.get("maxAttempts", 3)

        # self.logger.info(f"成功条件: {success_condition}")
        # self.logger.info(f"期望关键词: {expected_keywords_str}")
        # self.logger.info(f"期望短语: {expected_phrases_str}")
        # self.logger.info(f"最大尝试次数: {max_attempts}")

        # 解析关键词和短语
        expected_keywords = self._parse_json_list(expected_keywords_str)
        expected_phrases = self._parse_json_list(expected_phrases_str)

        # self.logger.info(f"解析后的期望关键词: {expected_keywords}")
        # self.logger.info(f"解析后的期望短语: {expected_phrases}")

        # 鼓励话语 & 替换姓名
        encouragement_message = step_config.get("encouragementMessage", "")
        child_name = session_data.get("child_name", "小朋友")

        print("-------------------评估结果-------------child_name--------------------------------", child_name)



        if encouragement_message:
            encouragement_message = encouragement_message.replace("{childName}", child_name).replace("{文杰}",
                                                                                                     child_name)

        print("------------------评估结果--------------encouragement_message--------------------------------", encouragement_message)


        # 清理输入 + 拼音
        user_text_clean = user_text.strip()
        user_text_lower = user_text_clean.lower()
        user_pinyin = self.pinyin.get_pinyin(user_text_clean, splitter=' ').lower()
        self.logger.info(f"用户输入拼音: {user_pinyin}")

        score = 0
        is_passed = False
        match_type = "no_match"
        feedback = encouragement_message or "请尝试更完整的回答。"
        max_similarity = 0  # 保留原字段（调试用）

        # ==================== 1. 完全匹配：包含任意短语（文字 OR 拼音） ====================
        if expected_phrases:
            for phrase in expected_phrases:
                phrase_clean = phrase.strip()
                phrase_lower = phrase_clean.lower()
                phrase_pinyin = self.pinyin.get_pinyin(phrase_clean, splitter=' ').lower()

                # 核心：包含完整短语（文字 or 拼音）
                if (phrase_lower in user_text_lower) or (phrase_pinyin in user_pinyin):
                    score = 100
                    is_passed = True
                    match_type = "perfect_match"
                    feedback =  "回答完全正确！"
                    self.logger.info(f"完全匹配：包含短语 '{phrase_clean}'（拼音: {phrase_pinyin}）")
                    break
                # else:
                #     # 保留原相似度计算（仅用于调试字段）
                #     sim = SequenceMatcher(None, user_text_lower, phrase_lower).ratio() * 100
                #     if sim > max_similarity:
                #         max_similarity = sim
                #     self.logger.info(f"短语相似度 '{phrase_lower}': {sim:.2f}%")

        # ==================== 2. 部分匹配：包含任意关键词（文字 OR 拼音） ====================
        if match_type != "perfect_match" and expected_keywords:
            for keyword in expected_keywords:
                keyword_clean = keyword.strip()
                keyword_lower = keyword_clean.lower()
                keyword_pinyin = self.pinyin.get_pinyin(keyword_clean, splitter=' ').lower()

                if (keyword_lower in user_text_lower) or (keyword_pinyin in user_pinyin):
                    score = 70
                    is_passed = True
                    match_type = "partial_match"
                    feedback = "回答得不错！"
                    self.logger.info(f"部分匹配：包含关键词 '{keyword_clean}'（拼音: {keyword_pinyin}）")
                    break

        # ==================== 3. 完全不匹配 ====================
        if match_type == "no_match":
            score = 0
            feedback = "再努力试试！"
            self.logger.info("完全不匹配")

        self.logger.info(f"匹配结果: match_type={match_type}, score={score}, is_passed={is_passed}")

        # 结果（完全保留原字段）
        result = {
            "score": score,
            "is_passed": is_passed,
            "feedback": feedback,
            "success_condition": match_type,
            "user_input": user_text,
            "expected_keywords": expected_keywords,
            "expected_phrases": expected_phrases,
            "max_phrase_similarity": max_similarity
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
        # self.logger.info("当前所有步骤的ID信息:")
        for i, step in enumerate(steps):
            self.logger.info(
                f"  步骤{i+1}: id={step.get('id')}, stepId={step.get('stepId')}, stepCode={step.get('stepCode')}")

        # 尝试多种ID字段匹配
        for i, step in enumerate(steps):
            # 匹配 stepId 字段
            if step.get("stepId") == step_id:
                self.logger.info(f"通过stepId找到步骤ID {step_id}，步骤为 {i+1}")
                return i
            # 匹配 id 字段
            if step.get("id") == step_id:
                self.logger.info(f"通过id字段找到步骤ID {step_id}，步骤为 {i+1}")
                return i
            # 匹配 stepCode 字段
            if step.get("stepCode") == step_id:
                self.logger.info(f"通过stepCode找到步骤ID {step_id}，步骤为 {i+1}")
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
        # 检查是否有任何分支配置 - 需要检查字段是否存在且非空字符串
        perfect_match = step_config.get("perfectMatchNextStepId", "").strip()
        exact_match = step_config.get("exactMatchStepId", "").strip()
        partial_match = step_config.get("partialMatchNextStepId", "").strip()
        partial_match_alt = step_config.get("partialMatchStepId", "").strip()
        no_match = step_config.get("noMatchNextStepId", "").strip()
        no_match_alt = step_config.get("noMatchStepId", "").strip()

        has_branch_config = bool(
            perfect_match or exact_match or partial_match or
            partial_match_alt or no_match or no_match_alt
        )

        is_leaf = not has_branch_config
        self.logger.info(f"步骤分支配置检查:")
        self.logger.info(f"  - perfectMatchNextStepId: '{perfect_match}'")
        self.logger.info(f"  - exactMatchStepId: '{exact_match}'")
        self.logger.info(f"  - partialMatchNextStepId: '{partial_match}'")
        self.logger.info(f"  - partialMatchStepId: '{partial_match_alt}'")
        self.logger.info(f"  - noMatchNextStepId: '{no_match}'")
        self.logger.info(f"  - noMatchStepId: '{no_match_alt}'")
        self.logger.info(f"  - 有分支配置: {has_branch_config}")
        self.logger.info(f"  - 是否为叶子节点: {is_leaf}")
        return is_leaf

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
