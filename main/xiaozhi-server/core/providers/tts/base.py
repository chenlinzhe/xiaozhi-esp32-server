import os
import re
import queue
import uuid
import asyncio
import threading
from core.utils import p3
from datetime import datetime
from core.utils import textUtils
from abc import ABC, abstractmethod
from config.logger import setup_logging
from core.utils.util import audio_to_data, audio_bytes_to_data
from core.utils.tts import MarkdownCleaner
from core.utils.output_counter import add_device_output
from core.handle.reportHandle import enqueue_tts_report
from core.handle.sendAudioHandle import sendAudioMessage
from core.providers.tts.dto.dto import (
    TTSMessageDTO,
    SentenceType,
    ContentType,
    InterfaceType,
)

import traceback

TAG = __name__
logger = setup_logging()


class TTSProviderBase(ABC):
    def __init__(self, config, delete_audio_file):
        self.interface_type = InterfaceType.NON_STREAM
        self.conn = None
        self.tts_timeout = 10
        self.delete_audio_file = delete_audio_file
        self.audio_file_type = "wav"
        self.output_file = config.get("output_dir", "tmp/")
        self.tts_text_queue = queue.Queue()
        self.tts_audio_queue = queue.Queue()
        self.tts_audio_first_sentence = True
        self.before_stop_play_files = []

        self.tts_text_buff = []
        self.punctuations = (
            "。",
            "？",
            "?",
            "！",
            "!",
            "；",
            ";",
            "：",
            "~",
        )
        self.first_sentence_punctuations = (
            "。",
            "？",
            "?",
            "！",
            "!",
            "；",
            ";",
            "：",
        )
        self.tts_stop_request = False
        self.processed_chars = 0
        self.is_first_sentence = True
        # 说话间隔等待时间（秒）
        self.speech_interval_wait = config.get("speech_interval_wait", 1.0)

    def generate_filename(self, extension=".wav"):
        return os.path.join(
            self.output_file,
            f"tts-{datetime.now().date()}@{uuid.uuid4().hex}{extension}",
        )

    def to_tts(self, text, speech_rate=None):
        text = MarkdownCleaner.clean_markdown(text)
        max_repeat_time = 5
        if self.delete_audio_file:
            # 需要删除文件的直接转为音频数据
            while max_repeat_time > 0:
                try:
                    # 使用新的事件循环来运行异步方法
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        audio_bytes = loop.run_until_complete(self.text_to_speak(text, None, speech_rate))
                        if audio_bytes:
                            audio_datas, _ = audio_bytes_to_data(
                                audio_bytes, file_type=self.audio_file_type, is_opus=True
                            )
                            return audio_datas
                        else:
                            max_repeat_time -= 1
                    finally:
                        loop.close()
                except Exception as e:
                    logger.bind(tag=TAG).warning(
                        f"语音生成失败{5 - max_repeat_time + 1}次: {text}，错误: {e}"
                    )
                    max_repeat_time -= 1
            if max_repeat_time > 0:
                logger.bind(tag=TAG).info(
                    f"语音生成成功: {text}，重试{5 - max_repeat_time}次"
                )
            else:
                logger.bind(tag=TAG).error(
                    f"语音生成失败: {text}，请检查网络或服务是否正常"
                )
            return None
        else:
            tmp_file = self.generate_filename()
            try:
                while not os.path.exists(tmp_file) and max_repeat_time > 0:
                    try:
                        # 使用新的事件循环来运行异步方法
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(self.text_to_speak(text, tmp_file, speech_rate))
                        finally:
                            loop.close()
                    except Exception as e:
                        logger.bind(tag=TAG).warning(
                            f"语音生成失败{5 - max_repeat_time + 1}次: {text}，错误: {e}"
                        )
                        # 未执行成功，删除文件
                        if os.path.exists(tmp_file):
                            os.remove(tmp_file)
                        max_repeat_time -= 1

                if max_repeat_time > 0:
                    logger.bind(tag=TAG).info(
                        f"语音生成成功: {text}:{tmp_file}，重试{5 - max_repeat_time}次"
                    )
                else:
                    logger.bind(tag=TAG).error(
                        f"语音生成失败: {text}，请检查网络或服务是否正常"
                    )

                return tmp_file
            except Exception as e:
                logger.bind(tag=TAG).error(f"Failed to generate TTS file: {e}")
                return None

    @abstractmethod
    async def text_to_speak(self, text, output_file, speech_rate=None):
        pass

    def audio_to_pcm_data(self, audio_file_path):
        """音频文件转换为PCM编码"""
        return audio_to_data(audio_file_path, is_opus=False)

    def audio_to_opus_data(self, audio_file_path):
        """音频文件转换为Opus编码"""
        return audio_to_data(audio_file_path, is_opus=True)

    def tts_one_sentence(
        self,
        conn,
        content_type,
        content_detail=None,
        content_file=None,
        sentence_id=None,
    ):
        """发送一句话"""
        if not sentence_id:
            if conn.sentence_id:
                sentence_id = conn.sentence_id
            else:
                sentence_id = str(uuid.uuid4().hex)
                conn.sentence_id = sentence_id
        
        # 发送FIRST请求开始TTS会话
        self.tts_text_queue.put(
            TTSMessageDTO(
                sentence_id=sentence_id,
                sentence_type=SentenceType.FIRST,
                content_type=ContentType.ACTION,
            )
        )
        
        # 对于单句的文本，进行分段处理
        if content_detail:
            segments = re.split(r"([。！？!?；;\n])", content_detail)
            for i, seg in enumerate(segments):
                if seg.strip():  # 只处理非空段
                    self.tts_text_queue.put(
                        TTSMessageDTO(
                            sentence_id=sentence_id,
                            sentence_type=SentenceType.MIDDLE,
                            content_type=content_type,
                            content_detail=seg,
                            content_file=content_file,
                        )
                    )
                    # 在句子之间添加等待时间（除了最后一个句子）
                    if i < len(segments) - 1 and self.speech_interval_wait > 0:
                        self.tts_text_queue.put(
                            TTSMessageDTO(
                                sentence_id=sentence_id,
                                sentence_type=SentenceType.MIDDLE,
                                content_type=ContentType.ACTION,
                                content_detail=f"__WAIT__{self.speech_interval_wait}",
                            )
                        )
        
        # 发送LAST请求结束TTS会话
        self.tts_text_queue.put(
            TTSMessageDTO(
                sentence_id=sentence_id,
                sentence_type=SentenceType.LAST,
                content_type=ContentType.ACTION,
            )
        )

    async def open_audio_channels(self, conn):
        try:
            self.conn = conn
            self.tts_timeout = conn.config.get("tts_timeout", 10)
            
            # 简化初始化，只启动必要的线程
            logger.bind(tag=TAG).info("开始初始化TTS音频通道...")
            
            # tts 消化线程
            self.tts_priority_thread = threading.Thread(
                target=self.tts_text_priority_thread, daemon=True
            )
            self.tts_priority_thread.start()
            logger.bind(tag=TAG).info("TTS文本处理线程已启动")
            logger.bind(tag=TAG).info(f"TTS线程状态: {self.tts_priority_thread.is_alive()}")

            # 音频播放 消化线程
            self.audio_play_priority_thread = threading.Thread(
                target=self._audio_play_priority_thread, daemon=True
            )
            self.audio_play_priority_thread.start()
            # logger.bind(tag=TAG).info("TTS音频播放线程已启动")
            
            # 等待线程启动完成（减少等待时间）
            await asyncio.sleep(0.1)
            
            # 简单检查线程是否启动，不强制要求线程立即活跃
            if hasattr(self, 'tts_priority_thread') and hasattr(self, 'audio_play_priority_thread'):
                logger.bind(tag=TAG).info("TTS音频通道打开成功")
            else:
                raise Exception("TTS线程创建失败")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"TTS音频通道打开失败: {e}")
            # 不抛出异常，让系统继续运行
            logger.bind(tag=TAG).warning("TTS音频通道打开失败，但继续使用TTS实例")

    # 这里默认是非流式的处理方式
    # 流式处理方式请在子类中重写
    def tts_text_priority_thread(self):
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                logger.bind(tag=TAG).info(f"TTS文本处理线程收到消息: {message.sentence_type}, {message.content_type}, {message.content_detail}")
                
                if message.sentence_type == SentenceType.FIRST:
                    self.conn.client_abort = False
                if self.conn.client_abort:
                    logger.bind(tag=TAG).info("收到打断信息，终止TTS文本处理线程")
                    continue
                if message.sentence_type == SentenceType.FIRST:
                    # 初始化参数
                    self.tts_stop_request = False
                    self.processed_chars = 0
                    self.tts_text_buff = []
                    self.is_first_sentence = True
                    self.tts_audio_first_sentence = True
                    logger.bind(tag=TAG).info("TTS会话开始，初始化参数")
                
                if ContentType.TEXT == message.content_type:
                    # 检查是否是等待时间指令
                    if message.content_detail and message.content_detail.startswith("__WAIT__"):
                        try:
                            wait_time = float(message.content_detail.replace("__WAIT__", ""))
                            logger.bind(tag=TAG).info(f"等待 {wait_time} 秒...")
                            import time
                            time.sleep(wait_time)
                            logger.bind(tag=TAG).info(f"等待完成")
                        except ValueError:
                            logger.bind(tag=TAG).warning(f"无效的等待时间: {message.content_detail}")
                        continue
                    
                    self.tts_text_buff.append(message.content_detail)
                    segment_text = self._get_segment_text()
                    if segment_text:
                        logger.bind(tag=TAG).info(f"开始处理TTS文本: {segment_text}")
                        # 获取语速参数，如果消息中有则使用，否则使用默认值
                        speech_rate = getattr(message, 'speech_rate', None)
                        if speech_rate is not None:
                            logger.bind(tag=TAG).info(f"=== TTS文本处理线程 ===")
                            logger.bind(tag=TAG).info(f"消息语速配置: {speech_rate}倍速")
                            logger.bind(tag=TAG).info(f"消息内容: {segment_text}")
                        else:
                            logger.bind(tag=TAG).info(f"使用默认语速配置")
                        
                        if self.delete_audio_file:
                            audio_datas = self.to_tts(segment_text, speech_rate=speech_rate)
                            if audio_datas:
                                self.tts_audio_queue.put(
                                    (message.sentence_type, audio_datas, segment_text)
                                )
                                logger.bind(tag=TAG).info(f"TTS音频数据已放入队列: {len(audio_datas)} 个音频包")
                            else:
                                logger.bind(tag=TAG).error(f"TTS生成音频失败: {segment_text}")
                        else:
                            tts_file = self.to_tts(segment_text, speech_rate=speech_rate)
                            if tts_file:
                                audio_datas = self._process_audio_file(tts_file)
                                self.tts_audio_queue.put(
                                    (message.sentence_type, audio_datas, segment_text)
                                )
                                logger.bind(tag=TAG).info(f"TTS音频文件已处理并放入队列: {tts_file}")
                            else:
                                logger.bind(tag=TAG).error(f"TTS生成音频文件失败: {segment_text}")
                if ContentType.FILE == message.content_type:
                    self._process_remaining_text()
                    tts_file = message.content_file
                    if tts_file and os.path.exists(tts_file):
                        audio_datas = self._process_audio_file(tts_file)
                        self.tts_audio_queue.put(
                            (message.sentence_type, audio_datas, message.content_detail)
                        )
                        logger.bind(tag=TAG).info(f"音频文件已处理并放入队列: {tts_file}")

                if message.sentence_type == SentenceType.LAST:
                    self._process_remaining_text()
                    self.tts_audio_queue.put(
                        (message.sentence_type, [], message.content_detail)
                    )
                    logger.bind(tag=TAG).info("TTS会话结束")

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"处理TTS文本失败: {str(e)}, 类型: {type(e).__name__}, 堆栈: {traceback.format_exc()}"
                )
                continue

    def _audio_play_priority_thread(self):
        while not self.conn.stop_event.is_set():
            text = None
            try:
                try:
                    sentence_type, audio_datas, text = self.tts_audio_queue.get(
                        timeout=1
                    )
                except queue.Empty:
                    if self.conn.stop_event.is_set():
                        break
                    continue
                
                # logger.bind(tag=TAG).info(f"音频播放线程收到音频数据: {sentence_type}, {text}, {len(audio_datas) if audio_datas else 0} 个音频包")
                
                future = asyncio.run_coroutine_threadsafe(
                    sendAudioMessage(self.conn, sentence_type, audio_datas, text),
                    self.conn.loop,
                )
                future.result()
                # logger.bind(tag=TAG).info(f"------sendAudioMessage发送信息: {text}")
                
                if self.conn.max_output_size > 0 and text:
                    add_device_output(self.conn.headers.get("device-id"), len(text))
                enqueue_tts_report(self.conn, text, audio_datas)
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"audio_play_priority priority_thread: {text} {e}"
                )

    async def start_session(self, session_id):
        pass

    async def finish_session(self, session_id):
        pass

    async def close(self):
        """资源清理方法"""
        if hasattr(self, "ws") and self.ws:
            await self.ws.close()

    def _get_segment_text(self):
        # 合并当前全部文本并处理未分割部分
        full_text = "".join(self.tts_text_buff)
        current_text = full_text[self.processed_chars :]  # 从未处理的位置开始
        last_punct_pos = -1

        # 根据是否是第一句话选择不同的标点符号集合
        punctuations_to_use = (
            self.first_sentence_punctuations
            if self.is_first_sentence
            else self.punctuations
        )

        for punct in punctuations_to_use:
            pos = current_text.rfind(punct)
            if (pos != -1 and last_punct_pos == -1) or (
                pos != -1 and pos < last_punct_pos
            ):
                last_punct_pos = pos

        if last_punct_pos != -1:
            segment_text_raw = current_text[: last_punct_pos + 1]
            segment_text = textUtils.get_string_no_punctuation_or_emoji(
                segment_text_raw
            )
            self.processed_chars += len(segment_text_raw)  # 更新已处理字符位置

            # 如果是第一句话，在找到第一个逗号后，将标志设置为False
            if self.is_first_sentence:
                self.is_first_sentence = False

            return segment_text
        elif self.tts_stop_request and current_text:
            segment_text = current_text
            self.is_first_sentence = True  # 重置标志
            return segment_text
        else:
            return None

    def _process_audio_file(self, tts_file):
        """处理音频文件并转换为指定格式

        Args:
            tts_file: 音频文件路径
            content_detail: 内容详情

        Returns:
            tuple: (sentence_type, audio_datas, content_detail)
        """
        if tts_file.endswith(".p3"):
            audio_datas, _ = p3.decode_opus_from_file(tts_file)
        elif self.conn.audio_format == "pcm":
            audio_datas, _ = self.audio_to_pcm_data(tts_file)
        else:
            audio_datas, _ = self.audio_to_opus_data(tts_file)

        if (
            self.delete_audio_file
            and tts_file is not None
            and os.path.exists(tts_file)
            and tts_file.startswith(self.output_file)
        ):
            os.remove(tts_file)
        return audio_datas

    def _process_before_stop_play_files(self):
        for audio_datas, text in self.before_stop_play_files:
            self.tts_audio_queue.put((SentenceType.MIDDLE, audio_datas, text))
        self.before_stop_play_files.clear()
        self.tts_audio_queue.put((SentenceType.LAST, [], None))

    def _process_remaining_text(self):
        """处理剩余的文本并生成语音

        Returns:
            bool: 是否成功处理了文本
        """
        full_text = "".join(self.tts_text_buff)
        remaining_text = full_text[self.processed_chars :]
        if remaining_text:
            segment_text = textUtils.get_string_no_punctuation_or_emoji(remaining_text)
            if segment_text:
                if self.delete_audio_file:
                    audio_datas = self.to_tts(segment_text)
                    if audio_datas:
                        self.tts_audio_queue.put(
                            (SentenceType.MIDDLE, audio_datas, segment_text)
                        )
                else:
                    tts_file = self.to_tts(segment_text)
                    audio_datas = self._process_audio_file(tts_file)
                    self.tts_audio_queue.put(
                        (SentenceType.MIDDLE, audio_datas, segment_text)
                    )
                self.processed_chars += len(full_text)
                return True
        return False
