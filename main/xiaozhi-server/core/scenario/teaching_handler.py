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
    """
   处理聊天模式切换和教学模式逻辑

   Args:
       query: 用户输入的查询文本

   Returns:
       bool: 如果处理了特殊逻辑返回True，否则返回None继续正常流程
   """
    def handle_chat_mode(self, query: str) -> Optional[bool]:


        try:
            self.logger.bind(tag=TAG).info(f"处理聊天模式切换和教学模式逻辑")

            # 使用设备ID作为用户ID，如果没有则使用session_id
            user_id = self.connection.device_id if self.connection.device_id else self.connection.session_id

            # 检查当前聊天状态
            current_status = self.chat_status_manager.get_user_chat_status(user_id)
            self.logger.bind(tag=TAG).info(f"用户 {user_id} 当前聊天状态: {current_status}")

            # 异步处理用户输入
            future = asyncio.run_coroutine_threadsafe(
                self.chat_status_manager.handle_user_input(user_id, query, self.connection.child_name),
                self.connection.loop
            )

            print("in  -handle_chat_mode-------------------------------------: ",self.connection.child_name)
            result = future.result()

            # self.logger.bind(tag=TAG).info(f"聊天模式处理结果result---------------------------------------: {result}")

            if result and result.get("success"):
                action = result.get("action")
                ai_message = result.get("ai_message", "")

                print("test2---------------------------------------")       
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


                    else:
                        # 其他模式切换，不发送AI消息
                        self.logger.bind(tag=TAG).info(f"其他模式切换，不发送AI消息")

                    self.logger.bind(tag=TAG).info(f"聊天模式切换完成: {result.get('mode')}")



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

                    return True

                elif action in ["next_step", "retry", "retry_current_step", "perfect_match_next", "partial_match_next", "no_match_next"]:
                    # 教学步骤处理
                    # 确保教学模式中语音监听正常工作，清除just_woken_up标志
                    # if hasattr(self.connection, 'just_woken_up'):
                    #     self.connection.just_woken_up = False
                    #     self.logger.bind(tag=TAG).info("教学步骤处理：清除just_woken_up标志，确保语音监听正常")

                    # 优先使用步骤的AI消息，如果没有才使用评估反馈

                    print("test3---------------------------------------")   

                                        # 1. 发送完成消息（使用0.5倍语速）
                    self._send_tts_message(ai_message, speech_rate=0.5)    

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

                            print("test   3.2222---------------------------------------")        
                            message_sent = True
                        else:
                            # 没有消息列表，不发送任何消息
                            self.logger.bind(tag=TAG).info(f"⚠️ 步骤 {step_id} 没有配置消息列表，不发送消息")

                    # 如果没有发送步骤消息，使用评估反馈
                    if not message_sent:
                        evaluation = result.get("evaluation", {})
                        feedback = evaluation.get("feedback", "")
                        self.logger.bind(tag=TAG).info(f"没有步骤消息，检查评估反馈: {feedback}")

                        print("test   3.3333---------------------------------------")        

                        if feedback:
                            self.logger.bind(tag=TAG).info(f"✅ 使用评估反馈: {feedback}")
                            self._send_tts_message(feedback)


                        else:
                            self.logger.bind(tag=TAG).warning(f"❌ 没有找到任何消息内容")
                            # 如果没有评估反馈，发送默认提示
                            default_message = "请尝试更完整的回答。"
                            self.logger.bind(tag=TAG).info(f"✅ 使用默认提示: {default_message}")
                            self._send_tts_message(default_message)

                    print("test4---------------------------------------")        
                    self.logger.bind(tag=TAG).info(f"教学步骤处理完成了: {action}")

                    return True


                elif action == "completed":
                    # 教学完成，切换到自由模式
                    self.logger.bind(tag=TAG).info(f"教学完成，最终得分: {result.get('final_score')}")


                    print(f"ai_message--------------------------------------: {ai_message}")
                    
                    # 1. 发送完成消息（使用0.5倍语速）
                    self._send_tts_message(ai_message, speech_rate=0.5)
                    


                    
                    # 4. 发送自由对话欢迎消息（使用0.5倍语速）
                    free_chat_welcome = "现在我们可以自由聊天了，你想聊什么呢？"
                    self._send_tts_message(free_chat_welcome, speech_rate=0.5)

                    self.connection.llm_finish_task = True
                    self.connection.allow_interrupt = True
                    
                    # 🔥 切换到自由对话模式，设置自由对话提示词
                    free_chat_prompt = f"""你是一个孤独症儿童的教育陪伴助手。你的用户大概在6岁左右，你是{self.connection.child_name}的AI朋友，你叫海王星，现在处于自由聊天模式。

请遵循以下原则：
1. 用亲切、活泼的语气与{self.connection.child_name}交流，像朋友一样
2. 可以讲故事、聊天、回答问题、玩文字游戏
3. 鼓励孩子的好奇心和想象力，给予正面引导
4. 回答要简短有趣，适合儿童理解，避免过于复杂的表达
5. 保持耐心和热情，让{self.connection.child_name}感受到陪伴和关爱
6. 每次回复尽量不超过30个字，讲故事可以适当加长。
6. 如果{self.connection.child_name}说"讲故事"，直接讲一个适合儿童的有趣故事

当前时间：{{{{current_time}}}}"""
                    
                    self.connection.change_system_prompt(free_chat_prompt)
                    self.logger.bind(tag=TAG).info(f"✅ 已设置自由对话提示词，用户: {self.connection.child_name}")
                    
                    self.logger.bind(tag=TAG).info("教学完成处理结束，系统已切换到自由模式")
                    # 🔥 关键：返回 None 让LLM处理用户输入
                    return None



                elif action == "free_chat":
                    # 自由聊天模式，发送简单回复后继续正常流程
                    # self._send_tts_message(ai_message)
                    self.logger.bind(tag=TAG).info("自由聊天模式")
                    # 不返回True，让流程继续到正常的LLM处理
                    return None

                elif action == "warning_reminder":
                    # 警告提示
                    self._send_tts_message(ai_message)
                    self.logger.bind(tag=TAG).info("发出警告提示")

                    # 结束TTS会话，确保消息能发送到用户端
                    self._end_tts_session()
                    return True

                elif action == "final_reminder":
                    # 最终提醒
                    self._send_tts_message(ai_message)
                    self.logger.bind(tag=TAG).info("发出最终提醒")

                    # 结束TTS会话，确保消息能发送到用户端
                    self._end_tts_session()
                    return True

                elif action == "timeout_response":
                    # 超时自动回复
                    self._send_tts_message(ai_message)
                    self.logger.bind(tag=TAG).info("教学超时自动回复")


                    return True

            # 如果没有特殊处理，返回None继续正常流程
            self.logger.bind(tag=TAG).info(f"聊天模式处理完成，返回None继续正常流程")
            return None

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"处理聊天模式失败: {e}")
            self._end_tts_session()
            return None


    """
    发送单条TTS消息（带重试机制）

    Args:
        message: 要发送的消息文本
        speech_rate: 语速配置（0.5-2.0倍速，1.0为正常语速）
        wait_time: 等待时间（秒）
    """


    """发送单条TTS消息"""
    def _send_tts_message(self, message: str, speech_rate: float = 1.0, wait_time: int = 0):

        if not message:
            self.logger.bind(tag=TAG).warning("TTS消息为空，跳过发送")
            return


        try:


            self.connection.dialogue.put(Message(role="assistant", content=message))


            # 生成一个新的

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
            self.logger.bind(tag=TAG).info("---------发送TTS FIRST请求")


            # 🔥 关键：等待 WebSocket 连接建立完成
            self.logger.bind(tag=TAG).info("⏳ 等待 WebSocket 连接建立...")
            time.sleep(1.0)  # 给异步线程时间去建立连接
            self.logger.bind(tag=TAG).info("✅ 连接应该已建立，继续发送")



            # 发送文本消息
            self.connection.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.connection.sentence_id,
                    sentence_type=SentenceType.MIDDLE,
                    content_type=ContentType.TEXT,
                    content_detail=message,

                )
            )
            # self.logger.bind(tag=TAG).info(f"发送待TTS合成消息到队列: {message}")

                    # 2. 结束TTS会话
            self._end_tts_session()

            # 3. ⚠️ 新增：等待完成消息播放完成
            completion_duration = self._calculate_speech_duration(message, 1.0)
            self.logger.bind(tag=TAG).info(f"等待完成消息播放: {completion_duration:.2f}秒")
            time.sleep(completion_duration+3)


        except Exception as e:
            self.logger.bind(tag=TAG).error(f"发送待TTS合成消息失败: {e}")
            self._end_tts_session()
            raise


    """发送列表TTS消息"""
    def _send_message_list(self, message_list: List[Dict]):

        try:
            if not message_list:
                return

            # 开始播放列表前禁止打断
            self.connection.allow_interrupt = False


            # 遍历消息列表,只发送 MIDDLE 类型的文本消息
            for i, message in enumerate(message_list):


                #通知设备进入播放

                # from core.handle.sendAudioHandle import send_tts_message
                # await send_tts_message(conn, "start")


                content = message.get("messageContent", "")  
                if not content:  
                    continue  
                    
                # 替换占位符  
                # self.child_name = self.connection.child_name
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
                



                # 🔥 关键:为每条消息生成一个 sentence_id
                sentence_id = str(uuid.uuid4().hex)
                self.connection.sentence_id = sentence_id

                # 发送 FIRST 请求(只在开始时发送一次)
                self.connection.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=sentence_id,
                        sentence_type=SentenceType.FIRST,
                        content_type=ContentType.ACTION,
                        speech_rate=speech_rate,  # ✅ 添加语速参数
                    )
                )


                # 🔥 关键：等待 WebSocket 连接建立完成
                self.logger.bind(tag=TAG).info("⏳ 等待 WebSocket 连接建立...")
                time.sleep(1.0)  # 给异步线程时间去建立连接
                self.logger.bind(tag=TAG).info("✅ 连接应该已建立，继续发送")

                # 🔥 关键:只发送 MIDDLE 类型的文本消息
                self.connection.tts.tts_text_queue.put(
                    TTSMessageDTO(
                        sentence_id=sentence_id,
                        sentence_type=SentenceType.MIDDLE,
                        content_type=ContentType.TEXT,
                        content_detail=content,

                    )
                )
                self.logger.bind(tag=TAG).info(f"📝 -------------发送待TTS合成消息到队列: {content} (语速: {speech_rate}倍)")
                self.connection.dialogue.put(Message(role="assistant", content=content))


                if i == len(message_list) - 1:
                    self.connection.llm_finish_task = True


                #先发送结束TTS,再等待数秒后，才开启下一次连接。
                self._end_tts_session()


                # 智能计算等待时间：根据当前消息的文本和语速,加上配置的等待时间
                total_wait_time = self._calculate_speech_duration(content, speech_rate) + wait_time
                self.logger.bind(tag=TAG).info(f"第 {i+1} 句计算的播放时长: {total_wait_time:.2f}秒")


                time.sleep(total_wait_time)




            # 播放完成后恢复打断功能
            self.connection.allow_interrupt = True



        except Exception as e:
            self.logger.bind(tag=TAG).error(f"发送消息列表失败: {e}")
            self._end_tts_session()


    # 获取步骤的消息列表
    def _get_step_message_list(self, step_id: str) -> Optional[List[Dict]]:

        try:
            self.logger.bind(tag=TAG).info(f"🔍 获取步骤消息列表，步骤ID: {step_id}")
            message_list = get_step_messages(step_id)

            # self.logger.bind(tag=TAG).info(f"API返回结果: {message_list}")

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

    #结束TTS会话
    def _end_tts_session(self):

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
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"结束TTS会话失败: {e}")


    # 清理资源 确保TTS会话正确关闭
    def cleanup(self):

        try:
            # 检查是否有未关闭的TTS会话
            if self.connection.sentence_id:
                self.logger.bind(tag=TAG).warning(
                    f"检测到未关闭的TTS会话，sentence_id: {self.connection.sentence_id}，执行清理"
                )
                # 强制关闭TTS会话
                self._end_tts_session()
            else:
                self.logger.bind(tag=TAG).debug("没有需要清理的TTS会话")

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"清理资源失败: {e}")

    """
    根据字符数估算语音播放时间

    Args:
        text: 要播放的文本
        speech_rate: 语速倍率 (1.0为正常语速)

    Returns:
        float: 估算的播放时间（秒）
    """
    def _calculate_speech_duration(self, text: str, speech_rate: float = 1.0) -> float:

        if not text:
            return 0.0

        # 中文字符平均每秒3-4个，英文平均每秒8-10个
        # 这里使用保守估算：中文每秒3个字符，英文每秒8个字符
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_chars = len([c for c in text if c.isalpha()])
        other_chars = len(text) - chinese_chars - english_chars

        # 基础时间计算（秒）
        base_time = (chinese_chars / 4) + (english_chars / 8.0) + (other_chars / 5.0)

        # 根据语速调整
        actual_time = base_time / speech_rate

        # 最少0.5秒，避免时间过短
        return max(0.5, actual_time)
