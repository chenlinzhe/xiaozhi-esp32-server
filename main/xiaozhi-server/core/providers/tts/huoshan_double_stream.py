import os
import uuid
import json
import queue
import asyncio
import traceback
import websockets
from core.utils.tts import MarkdownCleaner
from config.logger import setup_logging
from core.utils import opus_encoder_utils
from core.utils.util import check_model_key
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType
from asyncio import Task


TAG = __name__
logger = setup_logging()

PROTOCOL_VERSION = 0b0001
DEFAULT_HEADER_SIZE = 0b0001

# Message Type:
FULL_CLIENT_REQUEST = 0b0001
AUDIO_ONLY_RESPONSE = 0b1011
FULL_SERVER_RESPONSE = 0b1001
ERROR_INFORMATION = 0b1111

# Message Type Specific Flags
MsgTypeFlagNoSeq = 0b0000  # Non-terminal packet with no sequence
MsgTypeFlagPositiveSeq = 0b1  # Non-terminal packet with sequence > 0
MsgTypeFlagLastNoSeq = 0b10  # last packet with no sequence
MsgTypeFlagNegativeSeq = 0b11  # Payload contains event number (int32)
MsgTypeFlagWithEvent = 0b100
# Message Serialization
NO_SERIALIZATION = 0b0000
JSON = 0b0001
# Message Compression
COMPRESSION_NO = 0b0000
COMPRESSION_GZIP = 0b0001

EVENT_NONE = 0
EVENT_Start_Connection = 1

EVENT_FinishConnection = 2

EVENT_ConnectionStarted = 50  # 成功建连

EVENT_ConnectionFailed = 51  # 建连失败（可能是无法通过权限认证）

EVENT_ConnectionFinished = 52  # 连接结束

# 上行Session事件
EVENT_StartSession = 100
EVENT_CancelSession = 101
EVENT_FinishSession = 102
# 下行Session事件
EVENT_SessionStarted = 150
EVENT_SessionCanceled = 151
EVENT_SessionFinished = 152

EVENT_SessionFailed = 153

# 上行通用事件
EVENT_TaskRequest = 200

# 下行TTS事件
EVENT_TTSSentenceStart = 350

EVENT_TTSSentenceEnd = 351

EVENT_TTSResponse = 352


class Header:
    def __init__(
        self,
        protocol_version=PROTOCOL_VERSION,
        header_size=DEFAULT_HEADER_SIZE,
        message_type: int = 0,
        message_type_specific_flags: int = 0,
        serial_method: int = NO_SERIALIZATION,
        compression_type: int = COMPRESSION_NO,
        reserved_data=0,
    ):
        self.header_size = header_size
        self.protocol_version = protocol_version
        self.message_type = message_type
        self.message_type_specific_flags = message_type_specific_flags
        self.serial_method = serial_method
        self.compression_type = compression_type
        self.reserved_data = reserved_data

    def as_bytes(self) -> bytes:
        return bytes(
            [
                (self.protocol_version << 4) | self.header_size,
                (self.message_type << 4) | self.message_type_specific_flags,
                (self.serial_method << 4) | self.compression_type,
                self.reserved_data,
            ]
        )


class Optional:
    def __init__(
        self, event: int = EVENT_NONE, sessionId: str = None, sequence: int = None
    ):
        self.event = event
        self.sessionId = sessionId
        self.errorCode: int = 0
        self.connectionId: str | None = None
        self.response_meta_json: str | None = None
        self.sequence = sequence

    # 转成 byte 序列
    def as_bytes(self) -> bytes:
        option_bytes = bytearray()
        if self.event != EVENT_NONE:
            option_bytes.extend(self.event.to_bytes(4, "big", signed=True))
        if self.sessionId is not None:
            session_id_bytes = str.encode(self.sessionId)
            size = len(session_id_bytes).to_bytes(4, "big", signed=True)
            option_bytes.extend(size)
            option_bytes.extend(session_id_bytes)
        if self.sequence is not None:
            option_bytes.extend(self.sequence.to_bytes(4, "big", signed=True))
        return option_bytes


class Response:
    def __init__(self, header: Header, optional: Optional):
        self.optional = optional
        self.header = header
        self.payload: bytes | None = None

    def __str__(self):
        return super().__str__()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.ws = None
        self.interface_type = InterfaceType.DUAL_STREAM
        self._monitor_task = None  # 监听任务引用
        self.appId = config.get("appid")
        self.access_token = config.get("access_token")
        self.cluster = config.get("cluster")
        self.resource_id = config.get("resource_id")
        if config.get("private_voice"):
            self.voice = config.get("private_voice")
        else:
            self.voice = config.get("speaker")
        self.ws_url = config.get("ws_url")
        self.authorization = config.get("authorization")
        self.header = {"Authorization": f"{self.authorization}{self.access_token}"}
        self.enable_two_way = True
        self.tts_text = ""
        self.speech_rate = config.get("speech_rate", 0)  # 默认语速为0，取值范围[-50,100]
        self._converted_speech_rate = 0  # 转换后的语速，用于实际TTS请求
        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=16000, channels=1, frame_size_ms=60
        )
        model_key_msg = check_model_key("TTS", self.access_token)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)

    def _convert_speech_rate(self, teaching_speech_rate: float) -> int:
        """
        将教学模式的语速(0.2-3.0倍速)转换为火山引擎TTS的语速参数(-50到100)
        
        Args:
            teaching_speech_rate: 教学模式语速，范围0.2-3.0，1.0为正常语速
            
        Returns:
            int: 火山引擎TTS语速参数，范围-50到100
        """
        # 限制输入范围
        teaching_speech_rate = max(0.2, min(3.0, teaching_speech_rate))
        
        # 新的转换公式：将0.2-3.0倍速映射到-50到100
        # 0.2倍速 → -50, 1.0倍速 → 0, 3.0倍速 → 100
        # 使用线性映射：(teaching_speech_rate - 0.2) / (3.0 - 0.2) * (100 - (-50)) + (-50)
        huoshan_speech_rate = int((teaching_speech_rate - 0.2) / 2.8 * 150 - 50)
        
        # 确保在火山引擎TTS的有效范围内
        huoshan_speech_rate = max(-50, min(100, huoshan_speech_rate))
        
        logger.bind(tag=TAG).info(f"语速转换: {teaching_speech_rate}倍速 → {huoshan_speech_rate}")
        return huoshan_speech_rate

    async def open_audio_channels(self, conn):
        try:
            logger.bind(tag=TAG).info("火山双流式TTS开始打开音频通道...")
            logger.bind(tag=TAG).info(f"conn对象: {conn}, stop_event: {getattr(conn, 'stop_event', 'None')}")
            await super().open_audio_channels(conn)
            logger.bind(tag=TAG).info("火山双流式TTS音频通道打开成功")
            logger.bind(tag=TAG).info(f"TTS线程启动后conn对象: {self.conn}, stop_event: {getattr(self.conn, 'stop_event', 'None')}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to open audio channels: {str(e)}")
            import traceback
            logger.bind(tag=TAG).error(f"异常堆栈: {traceback.format_exc()}")
            self.ws = None
            raise

    async def _ensure_connection(self):
        """建立新的WebSocket连接"""
        try:
            # 🔥 关键修复：检查现有连接状态
            if self.ws:
                try:
                    # 检查连接是否仍然有效 - 兼容不同的WebSocket对象类型
                    if hasattr(self.ws, 'closed') and self.ws.closed:
                        logger.bind(tag=TAG).warning(f"现有连接已关闭，需要重新建立")
                        self.ws = None
                    elif hasattr(self.ws, 'close_code') and self.ws.close_code is not None:
                        logger.bind(tag=TAG).warning(f"现有连接已关闭，关闭代码: {self.ws.close_code}")
                        self.ws = None
                    else:
                        # 尝试ping测试
                        await self.ws.ping()
                        logger.bind(tag=TAG).info(f"使用已有有效连接...")
                        return self.ws
                except (websockets.ConnectionClosed, websockets.InvalidState, Exception) as e:
                    logger.bind(tag=TAG).warning(f"现有连接无效，需要重新建立: {str(e)}")
                    self.ws = None
            
            logger.bind(tag=TAG).info("开始建立新连接...")
            ws_header = {
                "X-Api-App-Key": self.appId,
                "X-Api-Access-Key": self.access_token,
                "X-Api-Resource-Id": self.resource_id,
                "X-Api-Connect-Id": uuid.uuid4(),
            }
            self.ws = await websockets.connect(
                self.ws_url, 
                additional_headers=ws_header, 
                max_size=1000000000,
                ping_interval=20,  # 添加ping间隔
                ping_timeout=10,   # 添加ping超时
                close_timeout=10   # 添加关闭超时
            )
            logger.bind(tag=TAG).info("WebSocket连接建立成功")
            return self.ws
        except Exception as e:
            logger.bind(tag=TAG).error(f"建立连接失败: {str(e)}")
            self.ws = None
            raise

    def tts_text_priority_thread(self):
        """火山引擎双流式TTS的文本处理线程"""
        logger.bind(tag=TAG).info("[TTS线程] 进入tts_text_priority_thread")
        
        try:
            while not self.conn.stop_event.is_set():
                try:
                    logger.bind(tag=TAG).debug(f"TTS线程等待消息，队列大小: {self.tts_text_queue.qsize()}")
                    message = self.tts_text_queue.get(timeout=1)
                    logger.bind(tag=TAG).info(
                        f"收到TTS任务｜{message.sentence_type.name} ｜ {message.content_type.name} | 会话ID: {self.conn.sentence_id}"
                    )

                    logger.bind(tag=TAG).info(f"[TTS线程] 收到TTS任务: {message}")
                    

                    if message.sentence_type == SentenceType.FIRST:
                        self.conn.client_abort = False

                    if self.conn.client_abort:
                        try:
                            logger.bind(tag=TAG).info("收到打断信息，终止TTS文本处理线程")
                            asyncio.run_coroutine_threadsafe(
                                self.cancel_session(self.conn.sentence_id),
                                loop=self.conn.loop,
                            )
                            continue
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"取消TTS会话失败: {str(e)}")
                            continue

                    if message.sentence_type == SentenceType.FIRST:
                        # 初始化参数
                        try:
                            # 检查消息中是否有语速配置，如果有则转换并使用
                            if message.speech_rate is not None:
                                self._converted_speech_rate = self._convert_speech_rate(message.speech_rate)
                                logger.bind(tag=TAG).info(f"FIRST消息使用语速配置: {message.speech_rate}倍速 → {self._converted_speech_rate}")
                            
                            if not getattr(self.conn, "sentence_id", None): 
                                self.conn.sentence_id = uuid.uuid4().hex
                                logger.bind(tag=TAG).info(f"自动生成新的 会话ID: {self.conn.sentence_id}")

                            logger.bind(tag=TAG).info("开始启动TTS会话...")
                            future = asyncio.run_coroutine_threadsafe(
                                self.start_session(self.conn.sentence_id),
                                loop=self.conn.loop,
                            )
                            future.result()
                            self.before_stop_play_files.clear()
                            logger.bind(tag=TAG).info("TTS会话启动成功")
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"启动TTS会话失败: {str(e)}")
                            # 🔥 关键修复：启动失败时清理资源
                            try:
                                future = asyncio.run_coroutine_threadsafe(
                                    self.close(),
                                    loop=self.conn.loop,
                                )
                                future.result(timeout=5)  # 5秒超时
                            except Exception as close_error:
                                logger.bind(tag=TAG).error(f"清理TTS资源失败: {str(close_error)}")
                            continue

                    elif ContentType.TEXT == message.content_type:
                        if message.content_detail:
                            try:
                                # 检查消息中是否有语速配置，如果有则转换并使用
                                if message.speech_rate is not None:
                                    self._converted_speech_rate = self._convert_speech_rate(message.speech_rate)
                                    logger.bind(tag=TAG).info(f"使用消息中的语速配置: {message.speech_rate}倍速 → {self._converted_speech_rate}")
                                
                                logger.bind(tag=TAG).debug(
                                    f"开始发送TTS文本: {message.content_detail}"
                                )
                                future = asyncio.run_coroutine_threadsafe(
                                    self.text_to_speak(message.content_detail, None),
                                    loop=self.conn.loop,
                                )
                                future.result()
                                logger.bind(tag=TAG).debug("TTS文本发送成功")
                            except Exception as e:
                                logger.bind(tag=TAG).error(f"发送TTS文本失败: {str(e)}")
                                continue

                    elif ContentType.FILE == message.content_type:
                        logger.bind(tag=TAG).info(
                            f"添加音频文件到待播放列表: {message.content_file}"
                        )
                        if message.content_file and os.path.exists(message.content_file):
                            # 先处理文件音频数据
                            file_audio = self._process_audio_file(message.content_file)
                            self.before_stop_play_files.append(
                                (file_audio, message.content_detail)
                            )

                    if message.sentence_type == SentenceType.LAST:
                        try:
                            logger.bind(tag=TAG).info("开始结束TTS会话...")
                            future = asyncio.run_coroutine_threadsafe(
                                self.finish_session(self.conn.sentence_id),
                                loop=self.conn.loop,
                            )
                            future.result()
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"结束TTS会话失败: {str(e)}")
                            continue

                except queue.Empty:
                    continue
                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"处理TTS文本失败: {str(e)}, 类型: {type(e).__name__}, 堆栈: {traceback.format_exc()}"
                    )
                    continue
        except Exception as e:
            logger.bind(tag=TAG).error(f"TTS文本处理线程异常退出: {str(e)}, 堆栈: {traceback.format_exc()}")
        finally:
            logger.bind(tag=TAG).info("TTS文本处理线程退出")

    async def text_to_speak(self, text, _):
        """发送文本到TTS服务"""
        try:
            # 建立新连接
            if self.ws is None:
                logger.bind(tag=TAG).warning(f"WebSocket连接不存在，终止发送文本")
                return

            #  过滤Markdown
            filtered_text = MarkdownCleaner.clean_markdown(text)

            # 发送文本
            await self.send_text(self.voice, filtered_text, self.conn.sentence_id)
            return
        except Exception as e:
            logger.bind(tag=TAG).error(f"发送TTS文本失败: {str(e)}")
            if self.ws:
                try:
                    await self.ws.close()
                except:
                    pass
                self.ws = None
            raise

    async def start_session(self, session_id):
        logger.bind(tag=TAG).info(f"开始会话～～{session_id}")
        try:
            # 检查是否需要从队列中获取语速配置
            if self._converted_speech_rate == 0 and not self.tts_text_queue.empty():
                try:
                    # 预览队列中的消息，查找TEXT类型的消息
                    queue_items = []
                    while not self.tts_text_queue.empty():
                        item = self.tts_text_queue.get_nowait()
                        queue_items.append(item)
                        if item.content_type.name == "TEXT" and item.speech_rate is not None:
                            self._converted_speech_rate = self._convert_speech_rate(item.speech_rate)
                            logger.bind(tag=TAG).info(f"start_session中获取语速配置: {item.speech_rate}倍速 → {self._converted_speech_rate}")
                            break
                    
                    # 将消息放回队列
                    for item in reversed(queue_items):
                        self.tts_text_queue.put(item)
                except Exception as e:
                    logger.bind(tag=TAG).error(f"start_session中获取语速配置失败: {str(e)}")
            
            # 会话开始时检测上个会话的监听状态
            if (
                self._monitor_task is not None
                and isinstance(self._monitor_task, Task)
                and not self._monitor_task.done()
            ):
                logger.bind(tag=TAG).info("检测到未完成的上个会话，关闭监听任务和连接...")
                await self.close()

            # 🔥 关键修复：建立新连接并添加重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 建立新连接
                    await self._ensure_connection()
                    
                    # 启动监听任务
                    self._monitor_task = asyncio.create_task(self._start_monitor_tts_response())

                    header = Header(
                        message_type=FULL_CLIENT_REQUEST,
                        message_type_specific_flags=MsgTypeFlagWithEvent,
                        serial_method=JSON,
                    ).as_bytes()
                    optional = Optional(
                        event=EVENT_StartSession, sessionId=session_id
                    ).as_bytes()
                    payload = self.get_payload_bytes(
                        event=EVENT_StartSession, speaker=self.voice, speech_rate=self._converted_speech_rate
                    )
                    await self.send_event(self.ws, header, optional, payload)
                    logger.bind(tag=TAG).info("会话启动请求已发送")
                    break  # 成功发送，跳出重试循环
                    
                except (websockets.ConnectionClosed, Exception) as e:
                    logger.bind(tag=TAG).warning(f"启动会话失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        # 清理连接状态
                        self.ws = None
                        if self._monitor_task:
                            self._monitor_task.cancel()
                            self._monitor_task = None
                        # 等待一段时间后重试
                        await asyncio.sleep(1)
                    else:
                        # 最后一次尝试失败，抛出异常
                        raise
        except Exception as e:
            logger.bind(tag=TAG).error(f"启动会话失败: {str(e)}")
            # 确保清理资源
            await self.close()
            raise

    async def finish_session(self, session_id):
        logger.bind(tag=TAG).info(f"关闭会话～～{session_id}")
        try:
            if self.ws:
                header = Header(
                    message_type=FULL_CLIENT_REQUEST,
                    message_type_specific_flags=MsgTypeFlagWithEvent,
                    serial_method=JSON,
                ).as_bytes()
                optional = Optional(
                    event=EVENT_FinishSession, sessionId=session_id
                ).as_bytes()
                payload = str.encode("{}")
                await self.send_event(self.ws, header, optional, payload)
                logger.bind(tag=TAG).info("会话结束请求已发送")

                # 等待监听任务完成
                if self._monitor_task:
                    try:
                        await self._monitor_task
                    except Exception as e:
                        logger.bind(tag=TAG).error(
                            f"等待监听任务完成时发生错误: {str(e)}"
                        )
                    finally:
                        self._monitor_task = None

        except Exception as e:
            logger.bind(tag=TAG).error(f"关闭会话失败: {str(e)}")
            # 确保清理资源
            await self.close()
            raise

    async def cancel_session(self,session_id):
        logger.bind(tag=TAG).info(f"取消会话，释放服务端资源～～{session_id}")
        try:
            if self.ws:
                header = Header(
                    message_type=FULL_CLIENT_REQUEST,
                    message_type_specific_flags=MsgTypeFlagWithEvent,
                    serial_method=JSON,
                ).as_bytes()
                optional = Optional(
                    event=EVENT_CancelSession, sessionId=session_id
                ).as_bytes()
                payload = str.encode("{}")
                await self.send_event(self.ws, header, optional, payload)
                logger.bind(tag=TAG).info("会话取消请求已发送")
        except Exception as e:
            logger.bind(tag=TAG).error(f"取消会话失败: {str(e)}")
            # 确保清理资源
            await self.close()
            raise

    async def close(self):
        """资源清理方法"""
        # 取消监听任务
        if self._monitor_task:
            try:
                self._monitor_task.cancel()
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.bind(tag=TAG).warning(f"关闭时取消监听任务错误: {e}")
            self._monitor_task = None

        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None

    async def _start_monitor_tts_response(self):
        """监听TTS响应"""
        opus_datas_cache = []
        is_first_sentence = True
        first_sentence_segment_count = 0  # 添加计数器
        try:
            session_finished = False  # 标记会话是否正常结束
            while not self.conn.stop_event.is_set():
                try:
                    # 确保 `recv()` 运行在同一个 event loop
                    msg = await self.ws.recv()
                    res = self.parser_response(msg)
                    self.print_response(res, "send_text res:")

                    if res.optional.event == EVENT_SessionCanceled:
                        logger.bind(tag=TAG).debug(f"释放服务端资源成功～～")
                        session_finished = True
                        break
                    elif res.optional.event == EVENT_TTSSentenceStart:
                        json_data = json.loads(res.payload.decode("utf-8"))
                        self.tts_text = json_data.get("text", "")
                        logger.bind(tag=TAG).debug(f"句子语音生成开始: {self.tts_text}")
                        self.tts_audio_queue.put(
                            (SentenceType.FIRST, [], self.tts_text)
                        )
                        opus_datas_cache = []
                        first_sentence_segment_count = 0  # 重置计数器
                    elif (
                        res.optional.event == EVENT_TTSResponse
                        and res.header.message_type == AUDIO_ONLY_RESPONSE
                    ):
                        logger.bind(tag=TAG).debug(f"推送数据到队列里面～～")
                        opus_datas = self.wav_to_opus_data_audio_raw(res.payload)
                        logger.bind(tag=TAG).debug(
                            f"推送数据到队列里面帧数～～{len(opus_datas)}"
                        )
                        if is_first_sentence:
                            first_sentence_segment_count += 1
                            if first_sentence_segment_count <= 6:
                                self.tts_audio_queue.put(
                                    (SentenceType.MIDDLE, opus_datas, None)
                                )
                            else:
                                opus_datas_cache.extend(opus_datas)
                        else:
                            # 后续句子缓存
                            opus_datas_cache.extend(opus_datas)
                    elif res.optional.event == EVENT_TTSSentenceEnd:
                        logger.bind(tag=TAG).info(f"句子语音生成成功：{self.tts_text}")
                        if not is_first_sentence or first_sentence_segment_count > 10:
                            # 发送缓存的数据
                            self.tts_audio_queue.put(
                                (SentenceType.MIDDLE, opus_datas_cache, None)
                            )
                        # 第一句话结束后，将标志设置为False
                        is_first_sentence = False
                    elif res.optional.event == EVENT_SessionFinished:
                        logger.bind(tag=TAG).debug(f"会话结束～～")
                        self._process_before_stop_play_files()
                        session_finished = True
                        break
                except websockets.ConnectionClosed:
                    logger.bind(tag=TAG).warning("WebSocket连接已关闭")
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"Error in _start_monitor_tts_response: {e}"
                    )
                    traceback.print_exc()
                    break
            # 仅在连接异常时才关闭
            if not session_finished and self.ws:
                try:
                    await self.ws.close()
                except:
                    pass
                self.ws = None
        # 监听任务退出时清理引用
        finally:
            self._monitor_task = None

    async def send_event(
        self,
        ws: websockets.WebSocketClientProtocol,
        header: bytes,
        optional: bytes | None = None,
        payload: bytes = None,
    ):
        try:
            # 🔥 关键修复：发送前检查连接状态
            if not ws:
                logger.bind(tag=TAG).error(f"WebSocket连接不存在，无法发送数据")
                raise websockets.ConnectionClosed(None, None)
            
            # 检查连接状态 - 兼容不同的WebSocket对象类型
            try:
                # 尝试检查连接状态
                if hasattr(ws, 'closed') and ws.closed:
                    logger.bind(tag=TAG).error(f"WebSocket连接已关闭，无法发送数据")
                    raise websockets.ConnectionClosed(None, None)
                elif hasattr(ws, 'close_code') and ws.close_code is not None:
                    logger.bind(tag=TAG).error(f"WebSocket连接已关闭，关闭代码: {ws.close_code}")
                    raise websockets.ConnectionClosed(ws.close_code, ws.close_reason)
            except AttributeError:
                # 如果WebSocket对象没有closed属性，尝试ping测试
                try:
                    await ws.ping()
                except Exception as ping_error:
                    logger.bind(tag=TAG).error(f"WebSocket连接ping失败: {str(ping_error)}")
                    raise websockets.ConnectionClosed(None, None)
            
            full_client_request = bytearray(header)
            if optional is not None:
                full_client_request.extend(optional)
            if payload is not None:
                payload_size = len(payload).to_bytes(4, "big", signed=True)
                full_client_request.extend(payload_size)
                full_client_request.extend(payload)
            
            await ws.send(full_client_request)
            logger.bind(tag=TAG).debug(f"成功发送TTS事件数据，大小: {len(full_client_request)} 字节")
            
        except websockets.ConnectionClosed as e:
            logger.bind(tag=TAG).error(f"WebSocket连接已关闭: {e}")
            # 清理连接状态
            self.ws = None
            raise
        except Exception as e:
            logger.bind(tag=TAG).error(f"发送TTS事件失败: {str(e)}")
            raise

    async def send_text(self, speaker: str, text: str, session_id):
        # 检查是否需要从队列中获取语速配置
        if self._converted_speech_rate == 0 and not self.tts_text_queue.empty():
            try:
                # 预览队列中的消息，查找TEXT类型的消息
                queue_items = []
                while not self.tts_text_queue.empty():
                    item = self.tts_text_queue.get_nowait()
                    queue_items.append(item)
                    if item.content_type.name == "TEXT" and item.speech_rate is not None:
                        self._converted_speech_rate = self._convert_speech_rate(item.speech_rate)
                        logger.bind(tag=TAG).info(f"从队列消息中获取语速配置: {item.speech_rate}倍速 → {self._converted_speech_rate}")
                        break
                
                # 将消息放回队列
                for item in reversed(queue_items):
                    self.tts_text_queue.put(item)
            except Exception as e:
                logger.bind(tag=TAG).error(f"从队列获取语速配置失败: {str(e)}")
        
        logger.bind(tag=TAG).info(f"发送文本到TTS服务，语速参数: {self._converted_speech_rate}")
        header = Header(
            message_type=FULL_CLIENT_REQUEST,
            message_type_specific_flags=MsgTypeFlagWithEvent,
            serial_method=JSON,
        ).as_bytes()
        optional = Optional(event=EVENT_TaskRequest, sessionId=session_id).as_bytes()
        payload = self.get_payload_bytes(
            event=EVENT_TaskRequest, text=text, speaker=speaker, speech_rate=self._converted_speech_rate
        )
        return await self.send_event(self.ws, header, optional, payload)

    # 读取 res 数组某段 字符串内容
    def read_res_content(self, res: bytes, offset: int):
        content_size = int.from_bytes(res[offset : offset + 4], "big", signed=True)
        offset += 4
        content = str(res[offset : offset + content_size])
        offset += content_size
        return content, offset

    # 读取 payload
    def read_res_payload(self, res: bytes, offset: int):
        payload_size = int.from_bytes(res[offset : offset + 4], "big", signed=True)
        offset += 4
        payload = res[offset : offset + payload_size]
        offset += payload_size
        return payload, offset

    def parser_response(self, res) -> Response:
        if isinstance(res, str):
            raise RuntimeError(res)
        response = Response(Header(), Optional())
        # 解析结果
        # header
        header = response.header
        num = 0b00001111
        header.protocol_version = res[0] >> 4 & num
        header.header_size = res[0] & 0x0F
        header.message_type = (res[1] >> 4) & num
        header.message_type_specific_flags = res[1] & 0x0F
        header.serialization_method = res[2] >> num
        header.message_compression = res[2] & 0x0F
        header.reserved = res[3]
        #
        offset = 4
        optional = response.optional
        if header.message_type == FULL_SERVER_RESPONSE or AUDIO_ONLY_RESPONSE:
            # read event
            if header.message_type_specific_flags == MsgTypeFlagWithEvent:
                optional.event = int.from_bytes(res[offset:8], "big", signed=True)
                offset += 4
                if optional.event == EVENT_NONE:
                    return response
                # read connectionId
                elif optional.event == EVENT_ConnectionStarted:
                    optional.connectionId, offset = self.read_res_content(res, offset)
                elif optional.event == EVENT_ConnectionFailed:
                    optional.response_meta_json, offset = self.read_res_content(
                        res, offset
                    )
                elif (
                    optional.event == EVENT_SessionStarted
                    or optional.event == EVENT_SessionFailed
                    or optional.event == EVENT_SessionFinished
                ):
                    optional.sessionId, offset = self.read_res_content(res, offset)
                    optional.response_meta_json, offset = self.read_res_content(
                        res, offset
                    )
                else:
                    optional.sessionId, offset = self.read_res_content(res, offset)
                    response.payload, offset = self.read_res_payload(res, offset)

        elif header.message_type == ERROR_INFORMATION:
            optional.errorCode = int.from_bytes(
                res[offset : offset + 4], "big", signed=True
            )
            offset += 4
            response.payload, offset = self.read_res_payload(res, offset)
        return response

    async def start_connection(self):
        header = Header(
            message_type=FULL_CLIENT_REQUEST,
            message_type_specific_flags=MsgTypeFlagWithEvent,
        ).as_bytes()
        optional = Optional(event=EVENT_Start_Connection).as_bytes()
        payload = str.encode("{}")
        return await self.send_event(self.ws, header, optional, payload)

    def print_response(self, res, tag_msg: str):
        logger.bind(tag=TAG).debug(f"===>{tag_msg} header:{res.header.__dict__}")
        logger.bind(tag=TAG).debug(f"===>{tag_msg} optional:{res.optional.__dict__}")

    def get_payload_bytes(
        self,
        uid="1234",
        event=EVENT_NONE,
        text="",
        speaker="",
        audio_format="pcm",
        audio_sample_rate=16000,
        speech_rate=0,
    ):
        # 如果传入的speech_rate是0，尝试从队列中获取语速配置
        if speech_rate == 0 and hasattr(self, 'tts_text_queue') and not self.tts_text_queue.empty():
            try:
                # 预览队列中的消息，查找TEXT类型的消息
                queue_items = []
                temp_items = []
                while not self.tts_text_queue.empty():
                    item = self.tts_text_queue.get_nowait()
                    temp_items.append(item)
                    if item.content_type.name == "TEXT" and item.speech_rate is not None:
                        # 转换教学模式语速到火山引擎格式
                        converted_rate = self._convert_speech_rate(item.speech_rate)
                        speech_rate = converted_rate
                        logger.bind(tag=TAG).info(f"get_payload_bytes中获取语速配置: {item.speech_rate}倍速 → {converted_rate}")
                        break
                
                # 将消息放回队列
                for item in reversed(temp_items):
                    self.tts_text_queue.put(item)
            except Exception as e:
                logger.bind(tag=TAG).error(f"get_payload_bytes中获取语速配置失败: {str(e)}")
        
        logger.bind(tag=TAG).info(f"get_payload_bytes最终使用语速参数: {speech_rate}")
        
        return str.encode(
            json.dumps(
                {
                    "user": {"uid": uid},
                    "event": event,
                    "namespace": "BidirectionalTTS",
                    "req_params": {
                        "text": text,
                        "speaker": speaker,
                        "audio_params": {
                            "format": audio_format,
                            "sample_rate": audio_sample_rate,
                            "speech_rate": speech_rate,
                        },
                    },
                }
            )
        )

    def wav_to_opus_data_audio_raw(self, raw_data_var, is_end=False):
        opus_datas = self.opus_encoder.encode_pcm_to_opus(raw_data_var, is_end)
        return opus_datas

    def to_tts(self, text: str) -> list:
        """非流式生成音频数据，用于生成音频及测试场景

        Args:
            text: 要转换的文本

        Returns:
            list: 音频数据列表
        """
        try:
            # 创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 生成会话ID
            session_id = uuid.uuid4().__str__().replace("-", "")

            # 存储音频数据
            audio_data = []

            async def _generate_audio():
                # 创建新的WebSocket连接
                ws_header = {
                    "X-Api-App-Key": self.appId,
                    "X-Api-Access-Key": self.access_token,
                    "X-Api-Resource-Id": self.resource_id,
                    "X-Api-Connect-Id": uuid.uuid4(),
                }
                ws = await websockets.connect(
                    self.ws_url, additional_headers=ws_header, max_size=1000000000
                )

                try:
                    # 启动会话
                    header = Header(
                        message_type=FULL_CLIENT_REQUEST,
                        message_type_specific_flags=MsgTypeFlagWithEvent,
                        serial_method=JSON,
                    ).as_bytes()
                    optional = Optional(
                        event=EVENT_StartSession, sessionId=session_id
                    ).as_bytes()
                    payload = self.get_payload_bytes(
                        event=EVENT_StartSession, speaker=self.voice, speech_rate=self._converted_speech_rate
                    )
                    await self.send_event(ws, header, optional, payload)

                    # 发送文本
                    header = Header(
                        message_type=FULL_CLIENT_REQUEST,
                        message_type_specific_flags=MsgTypeFlagWithEvent,
                        serial_method=JSON,
                    ).as_bytes()
                    optional = Optional(
                        event=EVENT_TaskRequest, sessionId=session_id
                    ).as_bytes()
                    payload = self.get_payload_bytes(
                        event=EVENT_TaskRequest, text=text, speaker=self.voice, speech_rate=self._converted_speech_rate
                    )
                    await self.send_event(ws, header, optional, payload)

                    # 发送结束会话请求
                    header = Header(
                        message_type=FULL_CLIENT_REQUEST,
                        message_type_specific_flags=MsgTypeFlagWithEvent,
                        serial_method=JSON,
                    ).as_bytes()
                    optional = Optional(
                        event=EVENT_FinishSession, sessionId=session_id
                    ).as_bytes()
                    payload = str.encode("{}")
                    await self.send_event(ws, header, optional, payload)

                    # 接收音频数据
                    while True:
                        msg = await ws.recv()
                        res = self.parser_response(msg)

                        if (
                            res.optional.event == EVENT_TTSResponse
                            and res.header.message_type == AUDIO_ONLY_RESPONSE
                        ):
                            opus_datas = self.wav_to_opus_data_audio_raw(res.payload)
                            audio_data.extend(opus_datas)
                        elif res.optional.event == EVENT_SessionFinished:
                            break

                finally:
                    # 清理资源
                    try:
                        await ws.close()
                    except:
                        pass

            # 运行异步任务
            loop.run_until_complete(_generate_audio())
            loop.close()

            return audio_data

        except Exception as e:
            logger.bind(tag=TAG).error(f"生成音频数据失败: {str(e)}")
            return []
