"""
场景教学处理器
负责处理场景教学相关的功能，包括聊天模式切换、教学会话管理、超时检查等
解决音频发送和用户接收问题，增强错误处理和日志记录
"""

import asyncio
import time
import uuid
import threading
import json
from typing import Dict, Any, Optional, List
from core.scenario.chat_status_manager import ChatStatusManager
from core.providers.tts.dto.dto import ContentType, TTSMessageDTO, SentenceType
from core.utils.dialogue import Message
from config.logger import setup_logging
from config.manage_api_client import get_step_messages

TAG = __name__


class TeachingHandler:
    """场景教学处理器"""

    def __init__(self, connection):
        """
        初始化教学处理器

        Args:
            connection: ConnectionHandler实例
        """
        self.connection = connection
        self.logger = setup_logging()
        self.chat_status_manager = ChatStatusManager()
        self.child_name = "小朋友"
        self.tts_send_retries = 3  # TTS发送重试次数
        self.audio_confirmation_timeout = 5  # 音频确认超时时间

    def set_child_name(self, child_name: str):
        """设置儿童姓名"""
        self.child_name = child_name

    def handle_chat_mode(self, query: str) -> Optional[bool]:
        """
        处理聊天模式切换和教学模式逻辑

        Args:
            query: 用户输入的查询文本

        Returns:
            bool: 如果处理了特殊逻辑返回True，否则返回None继续正常流程
        """
        try:
            self.logger.bind(tag=TAG).info(f"处理聊天模式切换和教学模式逻辑")

            # 使用设备ID作为用户ID，如果没有则使用session_id
            user_id = self.connection.device_id if self.connection.device_id else self.connection.session_id

            # 检查当前聊天状态
            current_status = self.chat_status_manager.get_user_chat_status(user_id)
            self.logger.bind(tag=TAG).info(f"用户 {user_id} 当前聊天状态: {current_status}")

            # 异步处理用户输入
            future = asyncio.run_coroutine_threadsafe(
                self.chat_status_manager.handle_user_input(user_id, query, self.child_name),
                self.connection.loop
            )
            result = future.result()

            self.logger.bind(tag=TAG).info(f"聊天模式处理结果: {result}")

            if result and result.get("success"):
                action = result.get("action")
                ai_message = result.get("ai_message", "")

                if action == "mode_switch":
                    # 模式切换，检查是否需要使用消息列表
                    self.logger.bind(tag=TAG).info(f"开始处理模式切换: {result.get('mode')}")
                    self.logger.bind(tag=TAG).info(f"AI消息内容: {ai_message}")
                    self.logger.bind(tag=TAG).info(f"result完整数据: {result}")

                    # 如果切换到教学模式，检查是否有消息列表
                    if result.get('mode') == 'teaching_mode':
                        # 确保教学模式中语音监听正常工作，清除just_woken_up标志
                        if hasattr(self.connection, 'just_woken_up'):
                            self.connection.just_woken_up = False
                            self.logger.bind(tag=TAG).info("教学模式切换：清除just_woken_up标志，确保语音监听正常")

                        current_step = result.get("current_step", {})
                        self.logger.bind(tag=TAG).info(f"current_step完整数据: {current_step}")

                        # 根据前端Vue代码分析，使用stepId字段获取消息列表
                        step_id = current_step.get("stepId")

                        self.logger.bind(tag=TAG).info(f"教学模式切换 - 步骤ID: {step_id}")
                        self.logger.bind(tag=TAG).info(f"步骤数据字段: stepId={current_step.get('stepId')}, id={current_step.get('id')}")

                        # 如果current_step为空，尝试从其他地方获取步骤ID
                        if not step_id and not current_step:
                            self.logger.bind(tag=TAG).warning("current_step为空，尝试从其他字段获取步骤信息")
                            # 检查是否有其他字段包含步骤信息
                            for key, value in result.items():
                                if isinstance(value, dict) and ('stepId' in value or 'id' in value):
                                    self.logger.bind(tag=TAG).info(f"在字段 {key} 中找到步骤数据: {value}")
                                    step_id = value.get("stepId") or value.get("id")
                                    break

                        if step_id:
                            # 尝试获取消息列表
                            message_list = self._get_step_message_list(step_id)
                            if message_list:
                                # 使用消息列表
                                self.logger.bind(tag=TAG).info(f"教学模式切换检测到消息列表，消息数量: {len(message_list)}")
                                self._send_message_list(message_list)
                            else:
                                # 没有消息列表，不发送任何消息
                                self.logger.bind(tag=TAG).info(f"步骤 {step_id} 没有配置消息列表，教学模式切换不发送消息")
                        else:
                            # 没有步骤ID，不发送任何消息
                            self.logger.bind(tag=TAG).info(f"没有步骤ID，教学模式切换不发送消息")

                        # 启动等待超时检查（延迟启动，等待TTS消息发送完成）
                        # wait_time = result.get("wait_time", 20)
                        # self.logger.bind(tag=TAG).info(f"教学模式，等待时间: {wait_time}")
                        # self._start_teaching_timeout_check_after_tts(user_id, wait_time)
                        self.logger.bind(tag=TAG).info("超时检查已禁用")
                    else:
                        # 其他模式切换，不发送AI消息
                        self.logger.bind(tag=TAG).info(f"其他模式切换，不发送AI消息")

                    self.logger.bind(tag=TAG).info(f"聊天模式切换完成: {result.get('mode')}")

                    # 发送LAST请求结束TTS会话
                    self._end_tts_session()

                    return True

                elif action == "start_teaching":
                    # 开始教学模式
                    # 确保教学模式中语音监听正常工作，清除just_woken_up标志
                    if hasattr(self.connection, 'just_woken_up'):
                        self.connection.just_woken_up = False
                        self.logger.bind(tag=TAG).info("开始教学：清除just_woken_up标志，确保语音监听正常")

                    # 检查是否有消息列表配置
                    current_step = result.get("current_step", {})
                    step_id = current_step.get("stepId") if current_step else None

                    self.logger.bind(tag=TAG).info(f"开始教学 - 步骤ID: {step_id}")

                    if step_id:
                        # 尝试获取消息列表
                        message_list = self._get_step_message_list(step_id)
                        if message_list:
                            # 使用消息列表
                            self.logger.bind(tag=TAG).info(f"开始教学检测到消息列表，消息数量: {len(message_list)}")
                            self._send_message_list(message_list)
                        else:
                            # 没有消息列表，不发送任何消息
                            self.logger.bind(tag=TAG).info(f"步骤 {step_id} 没有配置消息列表，开始教学不发送消息")
                    else:
                        # 没有步骤ID，不发送任何消息
                        self.logger.bind(tag=TAG).info(f"没有步骤ID，开始教学不发送消息")

                    self.logger.bind(tag=TAG).info(f"开始教学模式: {result.get('scenario_name')}")

                    # 结束TTS会话，确保消息能发送到用户端
                    self._end_tts_session()

                    # 启动等待超时检查（延迟启动，等待TTS消息发送完成）
                    # self._start_teaching_timeout_check_after_tts(user_id, result.get("timeoutSeconds", 20))
                    self.logger.bind(tag=TAG).info("超时检查已禁用")
                    return True

                elif action in ["next_step", "retry", "perfect_match_next", "partial_match_next", "no_match_next"]:
                    # 教学步骤处理
                    # 确保教学模式中语音监听正常工作，清除just_woken_up标志
                    if hasattr(self.connection, 'just_woken_up'):
                        self.connection.just_woken_up = False
                        self.logger.bind(tag=TAG).info("教学步骤处理：清除just_woken_up标志，确保语音监听正常")

                    # 优先使用步骤的AI消息，如果没有才使用评估反馈
                    current_step = result.get("current_step", {})
                    step_id = current_step.get("stepId") if current_step else None

                    self.logger.bind(tag=TAG).info(f"步骤配置 - 步骤ID: {step_id}")
                    self.logger.bind(tag=TAG).info(f"当前步骤详情: {current_step}")

                    # 检查评估信息
                    evaluation = result.get("evaluation", {})
                    self.logger.bind(tag=TAG).info(f"评估信息: {evaluation}")

                    message_sent = False

                    if step_id:
                        # 尝试获取消息列表
                        self.logger.bind(tag=TAG).info(f"尝试获取步骤 {step_id} 的消息列表...")
                        message_list = self._get_step_message_list(step_id)
                        if message_list:
                            # 使用消息列表
                            self.logger.bind(tag=TAG).info(f"✅ 检测到消息列表，消息数量: {len(message_list)}")
                            self._send_message_list(message_list)
                            message_sent = True
                        else:
                            # 没有消息列表，不发送任何消息
                            self.logger.bind(tag=TAG).info(f"⚠️ 步骤 {step_id} 没有配置消息列表，不发送消息")

                    # 如果没有发送步骤消息，使用评估反馈
                    if not message_sent:
                        evaluation = result.get("evaluation", {})
                        feedback = evaluation.get("feedback", "")
                        self.logger.bind(tag=TAG).info(f"没有步骤消息，检查评估反馈: {feedback}")
                        if feedback:
                            self.logger.bind(tag=TAG).info(f"✅ 使用评估反馈: {feedback}")
                            self._send_tts_message(feedback)
                            self.connection.dialogue.put(Message(role="assistant", content=feedback))
                        else:
                            self.logger.bind(tag=TAG).warning(f"❌ 没有找到任何消息内容")
                            # 如果没有评估反馈，发送默认提示
                            default_message = "请尝试更完整的回答。"
                            self.logger.bind(tag=TAG).info(f"✅ 使用默认提示: {default_message}")
                            self._send_tts_message(default_message)
                            self.connection.dialogue.put(Message(role="assistant", content=default_message))

                    self.logger.bind(tag=TAG).info(f"教学步骤处理完成: {action}")

                    # 结束TTS会话，确保消息能发送到用户端
                    self._end_tts_session()

                    # 重新启动等待超时检查（延迟启动，等待TTS消息发送完成）
                    # self._start_teaching_timeout_check_after_tts(user_id, result.get("timeoutSeconds", 20))
                    self.logger.bind(tag=TAG).info("超时检查已禁用")
                    return True

                elif action == "completed":
                    # 教学完成，切换到自由模式
                    # 只发送完成消息，不发送评估反馈
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info(f"教学完成，最终得分: {result.get('final_score')}")

                    # 结束TTS会话，确保消息能发送到用户端
                    self._end_tts_session()
                    return True

                elif action == "free_chat":
                    # 自由聊天模式，发送简单回复后继续正常流程
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info("自由聊天模式")
                    # 不返回True，让流程继续到正常的LLM处理
                    return None

                elif action == "warning_reminder":
                    # 警告提示
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info("发出警告提示")

                    # 结束TTS会话，确保消息能发送到用户端
                    self._end_tts_session()
                    return True

                elif action == "final_reminder":
                    # 最终提醒
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info("发出最终提醒")

                    # 结束TTS会话，确保消息能发送到用户端
                    self._end_tts_session()
                    return True

                elif action == "timeout_response":
                    # 超时自动回复
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self.logger.bind(tag=TAG).info("教学超时自动回复")

                    # 结束TTS会话，确保消息能发送到用户端
                    self._end_tts_session()
                    return True

            # 如果没有特殊处理，返回None继续正常流程
            self.logger.bind(tag=TAG).info(f"聊天模式处理完成，返回None继续正常流程")
            return None

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"处理聊天模式失败: {e}")
            return None

    def _send_tts_message(self, message: str, speech_rate: float = 1.0, wait_time: int = 0):
        """
        发送TTS消息（带重试机制）

        Args:
            message: 要发送的消息文本
            speech_rate: 语速配置（0.5-2.0倍速，1.0为正常语速）
            wait_time: 等待时间（秒）
        """
        self.logger.bind(tag=TAG).info(f"🎤 准备发送TTS消息: {message}")
        self.logger.bind(tag=TAG).info(f"TTS配置 - 语速: {speech_rate}倍速, 等待时间: {wait_time}秒")

        if not message:
            self.logger.bind(tag=TAG).warning("❌ TTS消息为空，跳过发送")
            return

        # 等待TTS初始化完成
        max_wait_time = 10  # 最多等待10秒
        wait_count = 0
        while not self.connection.tts and wait_count < max_wait_time:
            self.logger.bind(tag=TAG).info(f"等待TTS初始化... ({wait_count + 1}/{max_wait_time})")
            time.sleep(1)
            wait_count += 1

        if not self.connection.tts:
            self.logger.bind(tag=TAG).error("TTS初始化超时，无法发送消息")
            return

        # 重试机制
        for attempt in range(self.tts_send_retries):
            try:
                # 如果没有sentence_id，生成一个新的
                if not self.connection.sentence_id:
                    self.connection.sentence_id = str(uuid.uuid4().hex)
                    self.logger.bind(tag=TAG).info(f"生成新的sentence_id: {self.connection.sentence_id}")
                    # 发送FIRST请求
                    self.connection.tts.tts_text_queue.put(
                        TTSMessageDTO(
                            sentence_id=self.connection.sentence_id,
                            sentence_type=SentenceType.FIRST,
                            content_type=ContentType.ACTION,
                            speech_rate=speech_rate,
                        )
                    )
                    self.logger.bind(tag=TAG).info("发送TTS FIRST请求")

                # 发送文本消息到TTS队列
                self.connection.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=self.connection.sentence_id,
                        sentence_type=SentenceType.MIDDLE,
                        content_type=ContentType.TEXT,
                        content_detail=message,
                        speech_rate=speech_rate,
                    )
                )
                self.logger.bind(tag=TAG).info(f"发送TTS消息到队列 (尝试 {attempt + 1}/{self.tts_send_retries}): {message}")

                # 等待音频确认
                if self._wait_for_audio_confirmation():
                    self.logger.bind(tag=TAG).info(f"TTS消息发送成功 (尝试 {attempt + 1})")

                    # 如果有等待时间，发送等待指令
                    # if wait_time > 0:
                    #     self._send_wait_instruction(wait_time)
                    if wait_time > 0:
                        self.logger.bind(tag=TAG).info(f"等待指令已禁用，原等待时间: {wait_time}秒")

                    return
                else:
                    self.logger.bind(tag=TAG).warning(f"TTS消息发送可能失败 (尝试 {attempt + 1})")
                    if attempt < self.tts_send_retries - 1:
                        time.sleep(1)  # 等待1秒后重试

            except Exception as e:
                self.logger.bind(tag=TAG).error(f"发送TTS消息失败 (尝试 {attempt + 1}): {e}")
                if attempt < self.tts_send_retries - 1:
                    time.sleep(1)  # 等待1秒后重试

        self.logger.bind(tag=TAG).error(f"TTS消息发送失败，已重试 {self.tts_send_retries} 次")

    def _send_tts_message_simple(self, message: str, speech_rate: float = 1.0):
        """
        发送TTS消息（简化版本，不带重试机制）

        Args:
            message: 要发送的消息文本
            speech_rate: 语速配置（0.5-2.0倍速，1.0为正常语速）
        """
        if not message:
            self.logger.bind(tag=TAG).warning("TTS消息为空，跳过发送")
            return

        try:
            # 检查TTS连接状态
            if not self.connection.tts:
                self.logger.bind(tag=TAG).error("TTS实例不存在，无法发送消息")
                return

            # 🔥 关键修复：等待前一个TTS会话完全结束
            self._wait_for_previous_tts_session_completion()

            # 🔥 优化：为每条消息生成独立的sentence_id，确保消息独立发送
            sentence_id = str(uuid.uuid4().hex)
            self.logger.bind(tag=TAG).info(f"🎤 生成独立sentence_id: {sentence_id}")

            # 发送FIRST请求
            first_message = TTSMessageDTO(
                sentence_id=sentence_id,
                sentence_type=SentenceType.FIRST,
                content_type=ContentType.ACTION,
                speech_rate=speech_rate,
            )
            self.connection.tts.tts_text_queue.put(first_message)
            self.logger.bind(tag=TAG).info("📤 发送TTS FIRST请求")

            # 等待一小段时间确保FIRST请求被处理
            time.sleep(0.2)

            # 发送文本消息
            text_message = TTSMessageDTO(
                sentence_id=sentence_id,
                sentence_type=SentenceType.MIDDLE,
                content_type=ContentType.TEXT,
                content_detail=message,
                speech_rate=speech_rate,
            )
            self.connection.tts.tts_text_queue.put(text_message)
            self.logger.bind(tag=TAG).info(f"📝 发送TTS消息到队列: {message}")

            # 等待一小段时间确保文本消息被处理
            time.sleep(0.2)

            # 发送LAST请求
            last_message = TTSMessageDTO(
                sentence_id=sentence_id,
                sentence_type=SentenceType.LAST,
                content_type=ContentType.ACTION,
            )
            self.connection.tts.tts_text_queue.put(last_message)
            self.logger.bind(tag=TAG).info("📤 发送TTS LAST请求")

            # 🔥 优化：更新当前sentence_id，用于后续的音频确认
            self.connection.sentence_id = sentence_id

            # 等待一小段时间确保所有消息都被处理
            time.sleep(0.3)

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"发送TTS消息失败: {e}")

    def _get_step_message_list(self, step_id: str) -> Optional[List[Dict]]:
        """
        获取步骤的消息列表

        Args:
            step_id: 步骤ID

        Returns:
            List[Dict]: 消息列表，如果获取失败返回None
        """
        try:
            self.logger.bind(tag=TAG).info(f"🔍 获取步骤消息列表，步骤ID: {step_id}")
            message_list = get_step_messages(step_id)

            self.logger.bind(tag=TAG).info(f"API返回结果: {message_list}")

            if message_list and len(message_list) > 0:
                self.logger.bind(tag=TAG).info(f"✅ 获取到消息列表，消息数量: {len(message_list)}")
                for i, msg in enumerate(message_list):
                    self.logger.bind(tag=TAG).info(f"消息 {i+1}: {msg}")
                return message_list
            else:
                self.logger.bind(tag=TAG).info(f"⚠️ 步骤 {step_id} 没有配置消息列表或返回空结果")
                return None

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"❌ 获取步骤消息列表失败: {e}")
            return None

    def _send_message_list(self, message_list: List[Dict]):
        """
        发送消息列表

        Args:
            message_list: 消息列表，每个消息包含messageContent、speechRate、waitTimeSeconds等字段
        """
        try:
            self.logger.bind(tag=TAG).info(f"开始发送消息列表，消息数量: {len(message_list)}")

            for i, message in enumerate(message_list):
                # 获取消息内容
                content = message.get("messageContent", "")
                if not content:
                    self.logger.bind(tag=TAG).warning(f"消息 {i+1} 内容为空，跳过")
                    continue

                # 替换儿童姓名占位符
                content = content.replace("{文杰}", self.child_name)
                content = content.replace("{childName}", self.child_name)

                # 检查是否有重复的儿童姓名
                if f"{self.child_name}{self.child_name}" in content:
                    content = content.replace(f"{self.child_name}{self.child_name}", self.child_name)
                    self.logger.bind(tag=TAG).info(f"修复重复儿童姓名: {content}")

                # 获取语速配置（0.2-3.0倍速，1.0为正常语速，支持火山引擎双流TTS）
                speech_rate = float(message.get("speechRate", 1.0))
                self.logger.bind(tag=TAG).info(f"=== 消息列表语速配置 ===")
                self.logger.bind(tag=TAG).info(f"消息 {i+1} 原始speechRate: {message.get('speechRate')}")
                self.logger.bind(tag=TAG).info(f"消息 {i+1} 转换后speech_rate: {speech_rate}")
                self.logger.bind(tag=TAG).info(f"消息 {i+1} 语速范围检查: {speech_rate} (范围: 0.2-3.0)")

                if speech_rate < 0.2 or speech_rate > 3.0:
                    self.logger.bind(tag=TAG).warning(f"消息 {i+1} 语速配置超出范围(0.2-3.0)，使用默认值1.0")
                    speech_rate = 1.0
                else:
                    self.logger.bind(tag=TAG).info(f"消息 {i+1} 语速配置有效: {speech_rate}倍速")

                # 获取等待时间配置（秒）
                wait_time = int(message.get("waitTimeSeconds", 0))
                if wait_time < 0:
                    wait_time = 0
                    self.logger.bind(tag=TAG).warning(f"消息 {i+1} 等待时间配置无效，使用默认值0")

                # 获取消息类型
                message_type = message.get("messageType", "normal")

                self.logger.bind(tag=TAG).info(f"发送消息 {i+1}/{len(message_list)}: {content}")
                self.logger.bind(tag=TAG).info(f"消息配置 - 语速: {speech_rate}倍速, 等待时间: {wait_time}秒, 类型: {message_type}")
                self.logger.bind(tag=TAG).info(f"AI消息内容: {content}")
                self.logger.bind(tag=TAG).info(f"语速设置: {speech_rate}倍速")

                # 🔥 关键：在本句话说之前等待配置的时间
                if wait_time > 0:
                    self.logger.bind(tag=TAG).info(f"⏰ 本句话前等待 {wait_time} 秒...")
                    time.sleep(wait_time)

                # 为每条消息创建独立的TTS会话
                self._send_tts_message_simple(content, speech_rate)
                self.connection.dialogue.put(Message(role="assistant", content=content))

                # 🔥 关键：等待上一句话真正播放完成（不估算时间，不额外等待）
                self._wait_for_previous_message_completion()

            self.logger.bind(tag=TAG).info("消息列表发送完成")

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"发送消息列表失败: {e}")

    def _wait_for_audio_confirmation(self) -> bool:
        """
        等待音频确认

        Returns:
            bool: 是否收到音频确认
        """
        try:
            # 检查TTS音频队列是否有数据
            start_time = time.time()
            while time.time() - start_time < self.audio_confirmation_timeout:
                if not self.connection.tts.tts_audio_queue.empty():
                    self.logger.bind(tag=TAG).info("收到音频确认")
                    return True
                time.sleep(0.1)

            self.logger.bind(tag=TAG).warning("音频确认超时")
            return False

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"等待音频确认时出错: {e}")
            return False

    def _wait_for_audio_confirmation_quick(self) -> bool:
        """
        快速等待音频确认（非阻塞，超时时间较短）

        Returns:
            bool: 是否收到音频确认
        """
        try:
            # 快速检查TTS音频队列是否有数据（最多等待2秒）
            quick_timeout = 2.0
            start_time = time.time()
            while time.time() - start_time < quick_timeout:
                if not self.connection.tts.tts_audio_queue.empty():
                    self.logger.bind(tag=TAG).info("✅ 快速音频确认成功")
                    return True
                time.sleep(0.1)

            self.logger.bind(tag=TAG).info("ℹ️ 快速音频确认超时，继续使用估算时间")
            return False

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"快速音频确认时出错: {e}")
            return False

    def _wait_for_previous_tts_session_completion(self):
        """
        等待前一个TTS会话完全结束

        这是解决火山引擎TTS会话冲突的关键方法
        """
        try:
            self.logger.bind(tag=TAG).info("🔄 等待前一个TTS会话完全结束...")

            # 等待TTS文本队列清空
            max_wait_time = 5.0  # 增加到5秒，确保队列完全清空
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                if self.connection.tts.tts_text_queue.empty():
                    self.logger.bind(tag=TAG).info("✅ TTS文本队列已清空")
                    break
                time.sleep(0.1)

            # 等待音频播放完成
            audio_wait_time = 1.0  # 缩短到1秒
            self.logger.bind(tag=TAG).info(f"⏳ 等待音频播放完成 {audio_wait_time} 秒...")
            time.sleep(audio_wait_time)

            # 额外等待时间确保会话清理完成
            session_cleanup_wait = 1.0  # 缩短到1秒
            self.logger.bind(tag=TAG).info(f"⏳ 额外等待 {session_cleanup_wait} 秒确保会话清理完成...")
            time.sleep(session_cleanup_wait)

            self.logger.bind(tag=TAG).info("✅ 前一个TTS会话清理完成，可以发送新消息")

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"等待前一个TTS会话结束时出错: {e}")
            # 出错时使用更长的等待时间确保安全
            time.sleep(3.0)

    def _wait_for_previous_message_completion(self):
        """
        等待上一句话真正播放完成（不估算时间，不额外等待，只检测播放状态）
        """
        try:
            self.logger.bind(tag=TAG).info("🎵 开始监控上一句话播放完成...")

            # 1. 等待音频开始播放（检测音频队列有数据）
            audio_started = self._wait_for_audio_start_smart()
            if not audio_started:
                self.logger.bind(tag=TAG).info("ℹ️ 音频开始检测超时，继续发送下一条消息")
                return

            # 2. 等待音频播放完成（基于client_is_speaking状态）
            playback_completed = self._wait_for_audio_playback_end_real()
            if playback_completed:
                self.logger.bind(tag=TAG).info("✅ 检测到音频播放完成")
            else:
                self.logger.bind(tag=TAG).info("ℹ️ 音频播放完成检测超时，继续发送下一条消息")

            self.logger.bind(tag=TAG).info("✅ 上一句话播放完成监控结束")

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"监控上一句话播放完成时出错: {e}")

    def _wait_for_audio_start_smart(self) -> bool:
        """
        智能等待音频开始播放（基于音频队列检测）

        Returns:
            bool: 是否检测到音频开始播放
        """
        try:
            self.logger.bind(tag=TAG).info("🎤 智能等待音频开始播放...")

            # 等待音频队列有数据，表示音频开始生成
            max_wait_time = 5.0  # 最多等待5秒
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                if not self.connection.tts.tts_audio_queue.empty():
                    self.logger.bind(tag=TAG).info("✅ 检测到音频队列有数据，音频开始生成")
                    return True
                time.sleep(0.1)

            self.logger.bind(tag=TAG).info("ℹ️ 音频开始检测超时，继续使用估算时间")
            return False

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"智能等待音频开始时出错: {e}")
            return False

    def _wait_for_audio_playback_end_real(self) -> bool:
        """
        真正等待音频播放结束（基于client_is_speaking状态，不额外等待）

        Returns:
            bool: 是否检测到音频播放结束
        """
        try:
            self.logger.bind(tag=TAG).info("🔇 等待音频播放结束...")

            # 设置播放状态为True（因为音频开始播放）
            self.connection.client_is_speaking = True
            self.logger.bind(tag=TAG).info("🎤 设置播放状态为True")

            # 等待client_is_speaking变为False
            max_wait_time = 15.0  # 增加等待时间到15秒，确保长音频也能播放完成
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                if not self.connection.client_is_speaking:
                    self.logger.bind(tag=TAG).info("✅ 检测到音频播放结束")
                    return True
                time.sleep(0.1)

            self.logger.bind(tag=TAG).info("ℹ️ 音频播放结束检测超时，继续发送下一条消息")
            # 超时时手动清除播放状态
            self.connection.client_is_speaking = False
            return False

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"等待音频播放结束时出错: {e}")
            # 出错时确保播放状态被清除
            self.connection.client_is_speaking = False
            return False

    def _calculate_audio_duration(self, content: str) -> float:
        """
        计算音频播放时长

        Args:
            content: 文本内容

        Returns:
            float: 估算的播放时长（秒）
        """
        try:
            # 基础参数
            chars_per_second = 3.0  # 每秒约3个字符（中文）
            min_duration = 1.0      # 最小播放时长
            max_duration = 30.0     # 最大播放时长

            # 计算基础时长
            char_count = len(content)
            base_duration = char_count / chars_per_second

            # 考虑标点符号的停顿时间
            punctuation_count = content.count('。') + content.count('！') + content.count('？') + content.count('，')
            pause_time = punctuation_count * 0.3  # 每个标点符号增加0.3秒停顿

            # 总时长
            total_duration = base_duration + pause_time

            # 限制在合理范围内
            total_duration = max(min_duration, min(total_duration, max_duration))

            self.logger.bind(tag=TAG).debug(f"音频时长计算 - 字符数: {char_count}, 标点数: {punctuation_count}, 基础时长: {base_duration:.2f}s, 停顿时长: {pause_time:.2f}s, 总时长: {total_duration:.2f}s")

            return total_duration

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"计算音频时长时出错: {e}")
            return 3.0  # 默认3秒

    def _end_tts_session(self):
        """结束TTS会话"""
        try:
            if self.connection.sentence_id and self.connection.tts:
                self.connection.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=self.connection.sentence_id,
                        sentence_type=SentenceType.LAST,
                        content_type=ContentType.ACTION,
                    )
                )
                self.logger.bind(tag=TAG).info("发送TTS LAST请求")

                # 清空sentence_id，为下次会话做准备
                self.connection.sentence_id = None

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"结束TTS会话失败: {e}")


    def _start_teaching_timeout_check_after_tts(self, user_id: str, wait_time: int):
        """
        在TTS消息发送完成后启动教学超时检查

        Args:
            user_id: 用户ID
            wait_time: 等待时间（秒）
        """
        # 如果wait_time为0，不启动超时检查
        if wait_time <= 0:
            self.logger.bind(tag=TAG).info("不启动超时检查（立即开始）")
            return

        self.logger.bind(tag=TAG).info(f"TTS消息发送完成，延迟启动超时检查，总等待时间: {wait_time}秒")

        # 延迟启动超时检查，确保TTS消息完全发送完成
        def delayed_start():
            # 等待TTS消息发送完成（通常需要1-2秒）
            time.sleep(2)
            # 更新等待开始时间
            self.chat_status_manager.update_wait_start_time(user_id)
            self._start_teaching_timeout_check(user_id, wait_time)

        # 在新线程中执行延迟启动
        threading.Thread(target=delayed_start, daemon=True).start()

    def _start_teaching_timeout_check(self, user_id: str, wait_time: int):
        """
        启动教学超时检查 - 优化版本，支持渐进式提示

        Args:
            user_id: 用户ID
            wait_time: 等待时间（秒）
        """
        # 如果wait_time为0，不启动超时检查
        if wait_time <= 0:
            self.logger.bind(tag=TAG).info("不启动超时检查（立即开始）")
            return

        self.logger.bind(tag=TAG).info(f"启动渐进式超时检查，总等待时间: {wait_time}秒")

        async def progressive_timeout_check():
            """渐进式超时检查"""
            try:
                # 获取超时配置
                progressive_config = self.chat_status_manager.PROGRESSIVE_TIMEOUT_CONFIG
                warning_timeout = wait_time * progressive_config.get("warning_timeout", 0.7)
                final_timeout = wait_time * progressive_config.get("final_timeout", 0.9)

                self.logger.bind(tag=TAG).info(f"警告时间点: {warning_timeout}秒")
                self.logger.bind(tag=TAG).info(f"最终提醒时间点: {final_timeout}秒")

                # 检查警告提示
                if progressive_config.get("enabled", False):
                    await asyncio.sleep(warning_timeout)
                    result = await self.chat_status_manager.check_teaching_timeout(user_id)
                    if result and result.get("success") and result.get("action") == "warning_reminder":
                        ai_message = result.get("ai_message", "")
                        self._send_tts_message(ai_message)
                        self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                        self._end_tts_session()  # 结束TTS会话
                        self.logger.bind(tag=TAG).info("发出警告提示")

                    # 检查最终提醒
                    remaining_time = final_timeout - warning_timeout
                    if remaining_time > 0:
                        await asyncio.sleep(remaining_time)
                        result = await self.chat_status_manager.check_teaching_timeout(user_id)
                        if result and result.get("success") and result.get("action") == "final_reminder":
                            ai_message = result.get("ai_message", "")
                            self._send_tts_message(ai_message)
                            self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                            self._end_tts_session()  # 结束TTS会话
                            self.logger.bind(tag=TAG).info("发出最终提醒")

                # 最终超时检查
                remaining_time = wait_time - final_timeout
                if remaining_time > 0:
                    await asyncio.sleep(remaining_time)

                result = await self.chat_status_manager.check_teaching_timeout(user_id)
                if result and result.get("success") and result.get("action") == "timeout_response":
                    ai_message = result.get("ai_message", "")
                    self._send_tts_message(ai_message)
                    self.connection.dialogue.put(Message(role="assistant", content=ai_message))
                    self._end_tts_session()  # 结束TTS会话
                    self.logger.bind(tag=TAG).info("教学超时，发送替代提示")

            except Exception as e:
                self.logger.bind(tag=TAG).error(f"渐进式超时检查失败: {e}")

        # 在事件循环中执行超时检查
        try:
            asyncio.create_task(progressive_timeout_check())
        except RuntimeError as e:
            if "no running event loop" in str(e):
                # 如果没有运行的事件循环，使用run_coroutine_threadsafe
                asyncio.run_coroutine_threadsafe(progressive_timeout_check(), self.connection.loop)
            else:
                raise

    async def cleanup(self):
        """清理教学处理器资源"""
        try:
            if hasattr(self, "chat_status_manager") and self.chat_status_manager:
                user_id = self.connection.device_id if self.connection.device_id else self.connection.session_id
                self.chat_status_manager.redis_client.delete_session_data(f"teaching_{user_id}")
                self.logger.bind(tag=TAG).info(f"清理用户 {user_id} 的聊天会话数据")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"清理教学处理器资源失败: {e}")

    def get_connection_status(self) -> Dict[str, Any]:
        """
        获取连接状态信息

        Returns:
            Dict: 连接状态信息
        """
        try:
            return {
                "websocket_connected": self.connection.websocket is not None,
                "tts_available": self.connection.tts is not None,
                "sentence_id": self.connection.sentence_id,
                "device_id": self.connection.device_id,
                "session_id": self.connection.session_id,
                "last_activity": getattr(self.connection, 'last_activity_time', None)
            }
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"获取连接状态失败: {e}")
            return {"error": str(e)}
