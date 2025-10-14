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

            self.logger.bind(tag=TAG).info(f"聊天模式处理结果result---------------------------------------: {result}")

            if result and result.get("success"):
                action = result.get("action")
                ai_message = result.get("ai_message", "")


                print(f"action--------------------------------------: {action}")

                if action == "mode_switch":
                    # 模式切换，检查是否需要使用消息列表
                    self.logger.bind(tag=TAG).info(f"开始处理模式切换: {result.get('mode')}")
                    self.logger.bind(tag=TAG).info(f"AI消息内容 in handle_chat_mode: {ai_message}")
                    # self.logger.bind(tag=TAG).info(f"result完整数据: {result}")

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
            





        

    """
    发送单条TTS消息（带重试机制）

    Args:
        message: 要发送的消息文本
        speech_rate: 语速配置（0.5-2.0倍速，1.0为正常语速）
        wait_time: 等待时间（秒）
    """


    def _send_tts_message(self, message: str, speech_rate: float = 1.0, wait_time: int = 0):  
        """发送单条TTS消息"""  
        if not message:  
            self.logger.bind(tag=TAG).warning("TTS消息为空，跳过发送")  
            return  
    
        if not self.connection.tts:  
            self.logger.bind(tag=TAG).error("TTS实例不存在，无法发送消息")  
            return  
    
        try:  
            # 如果没有 sentence_id,生成一个新的  
            if not self.connection.sentence_id:  
                self.connection.sentence_id = str(uuid.uuid4().hex)  
                self.logger.bind(tag=TAG).info(f"生成新的sentence_id: {self.connection.sentence_id}")  
                
                # 发送 FIRST 请求  
                self.connection.tts.tts_text_queue.put(  
                    TTSMessageDTO(  
                        sentence_id=self.connection.sentence_id,  
                        sentence_type=SentenceType.FIRST,  
                        content_type=ContentType.ACTION,  
                        speech_rate=speech_rate,  
                    )  
                )  
                self.logger.bind(tag=TAG).info("发送TTS FIRST请求")  
    
            # 发送文本消息  
            self.connection.tts.tts_text_queue.put(  
                TTSMessageDTO(  
                    sentence_id=self.connection.sentence_id,  
                    sentence_type=SentenceType.MIDDLE,  
                    content_type=ContentType.TEXT,  
                    content_detail=message,  
                    speech_rate=speech_rate,  
                )  
            )  
            self.logger.bind(tag=TAG).info(f"发送TTS消息到队列: {message}")  
            
        except Exception as e:  
            self.logger.bind(tag=TAG).error(f"发送TTS消息失败: {e}")  
            raise

    """
    发送单条TTS消息（简化版本，不带重试机制），被_send_message_list调用

    Args:
        message: 要发送的消息文本
        speech_rate: 语速配置（0.5-2.0倍速，1.0为正常语速）
    """



    def _send_message_list(self, message_list: List[Dict]):

        try:  
            if not message_list:  
                return  
                
            # 🔥 关键:为整个消息列表生成一个 sentence_id  
            sentence_id = str(uuid.uuid4().hex)  
            self.connection.sentence_id = sentence_id  
            
            # 发送 FIRST 请求(只在开始时发送一次)  
            self.connection.tts.tts_text_queue.put(  
                TTSMessageDTO(  
                    sentence_id=sentence_id,  
                    sentence_type=SentenceType.FIRST,  
                    content_type=ContentType.ACTION,  
                )  
            )  
            self.logger.bind(tag=TAG).info("📤 发送TTS FIRST请求")  
            
            # 遍历消息列表,只发送 MIDDLE 类型的文本消息  
            for i, message in enumerate(message_list):  
                content = message.get("messageContent", "")  
                if not content:  
                    continue  
                    
                # 替换占位符  
                content = content.replace("{文杰}", self.child_name)  
                content = content.replace("{childName}", self.child_name)  
                if f"{self.child_name}{self.child_name}" in content:  
                    content = content.replace(f"{self.child_name}{self.child_name}", self.child_name)  
                
                # 获取配置  
                speech_rate = float(message.get("speechRate", 1.0))  
                if speech_rate < 0.2 or speech_rate > 3.0:  
                    speech_rate = 1.0  
                    
                wait_time = int(message.get("waitTimeSeconds", 0))  
                if wait_time < 0:  
                    wait_time = 0  
                
                self.logger.bind(tag=TAG).info(f"将要处理第 {i+1}/{len(message_list)}: {content}")  
                
                # 在本句话说之前等待  
                if wait_time > 0:  
                    self.logger.bind(tag=TAG).info(f"本句话前等待 {wait_time} 秒...")  
                    time.sleep(wait_time)
                
                # 🔥 关键:只发送 MIDDLE 类型的文本消息  
                self.connection.tts.tts_text_queue.put(  
                    TTSMessageDTO(  
                        sentence_id=sentence_id,  
                        sentence_type=SentenceType.MIDDLE,  
                        content_type=ContentType.TEXT,  
                        content_detail=content,  
                        speech_rate=speech_rate,  
                    )  
                )  
                self.logger.bind(tag=TAG).info(f"📝 发送TTS消息到队列: {content}")  
                self.connection.dialogue.put(Message(role="assistant", content=content))  
            
            # 🔥 关键:在所有消息发送完后,只发送一次 LAST 请求  
            self.connection.tts.tts_text_queue.put(  
                TTSMessageDTO(  
                    sentence_id=sentence_id,  
                    sentence_type=SentenceType.LAST,  
                    content_type=ContentType.ACTION,  
                )  
            )  
            self.logger.bind(tag=TAG).info("📤 发送TTS LAST请求")  
            
            self.logger.bind(tag=TAG).info("消息列表发送完成")  
            
        except Exception as e:  
            self.logger.bind(tag=TAG).error(f"发送消息列表失败: {e}")



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
                # self.logger.bind(tag=TAG).info(f"✅ 获取到消息列表，消息数量: {len(message_list)}")
                # for i, msg in enumerate(message_list):
                #     self.logger.bind(tag=TAG).info(f"消息 {i+1}: {msg}")
                return message_list
            else:
                self.logger.bind(tag=TAG).info(f"⚠️ 步骤 {step_id} 没有配置消息列表或返回空结果")
                return None

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"❌ 获取步骤消息列表失败: {e}")
            return None


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

    
