import os
import sys
import copy
import json
import uuid
import time
import queue
import asyncio
import threading
import traceback
import subprocess
import websockets
from core.utils.util import (
    extract_json_from_string,
    check_vad_update,
    check_asr_update,
    filter_sensitive_info,
)
from typing import Dict, Any
from collections import deque
from core.utils.modules_initialize import (
    initialize_modules,
    initialize_tts,
    initialize_asr,
)
from core.handle.reportHandle import report
from core.providers.tts.default import DefaultTTS
from concurrent.futures import ThreadPoolExecutor
from core.utils.dialogue import Message, Dialogue
from core.providers.asr.dto.dto import InterfaceType
from core.handle.textHandle import handleTextMessage
from core.providers.tools.unified_tool_handler import UnifiedToolHandler
from plugins_func.loadplugins import auto_import_modules
from plugins_func.register import Action, ActionResponse
from core.auth import AuthMiddleware, AuthenticationError
from config.config_loader import get_private_config_from_api
from core.providers.tts.dto.dto import ContentType, TTSMessageDTO, SentenceType

from config.logger import setup_logging, build_module_string, create_connection_logger
from config.manage_api_client import DeviceNotFoundException, DeviceBindException
from core.utils.prompt_manager import PromptManager
from core.utils.voiceprint_provider import VoiceprintProvider
from core.utils import textUtils
from core.scenario.teaching_handler import TeachingHandler

TAG = __name__

auto_import_modules("plugins_func.functions")


class TTSException(RuntimeError):
    pass


class ConnectionHandler:
    def __init__(
        self,
        config: Dict[str, Any],
        _vad,
        _asr,
        _llm,
        _memory,
        _intent,
        server=None,
    ):
        self.common_config = config
        self.config = copy.deepcopy(config)
        self.session_id = str(uuid.uuid4())
        self.logger = setup_logging()
        self.server = server  # 保存server实例的引用

        self.auth = AuthMiddleware(config)
        self.need_bind = False
        self.bind_code = None
        self.read_config_from_api = self.config.get("read_config_from_api", False)

        self.websocket = None
        self.headers = None
        self.device_id = None
        self.client_ip = None
        self.prompt = None
        self.welcome_msg = None
        self.max_output_size = 0
        self.chat_history_conf = 0
        self.audio_format = "opus"

        # 客户端状态相关
        self.client_abort = False
        self.client_is_speaking = False
        self.allow_interrupt = True


        self.client_listen_mode = "auto"

        # 线程任务相关
        self.loop = asyncio.get_event_loop()
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5)

        # 添加上报线程池
        self.report_queue = queue.Queue()
        self.report_thread = None
        # 未来可以通过修改此处，调节asr的上报和tts的上报，目前默认都开启
        self.report_asr_enable = self.read_config_from_api
        self.report_tts_enable = self.read_config_from_api

        # 依赖的组件
        self.vad = None
        self.asr = None
        self.tts = None
        self._asr = _asr
        self._vad = _vad
        self.llm = _llm
        self.memory = _memory
        self.intent = _intent

        # 为每个连接单独管理声纹识别
        self.voiceprint_provider = None

        # vad相关变量
        self.client_audio_buffer = bytearray()
        self.client_have_voice = False
        self.last_activity_time = 0.0  # 统一的活动时间戳（毫秒）
        self.client_voice_stop = False
        self.client_voice_window = deque(maxlen=5)
        self.last_is_voice = False

        # asr相关变量
        # 因为实际部署时可能会用到公共的本地ASR，不能把变量暴露给公共ASR
        # 所以涉及到ASR的变量，需要在这里定义，属于connection的私有变量
        self.asr_audio = []
        self.asr_audio_queue = queue.Queue()

        # llm相关变量
        self.llm_finish_task = True
        self.dialogue = Dialogue()

        # tts相关变量
        self.sentence_id = None
        # 处理TTS响应没有文本返回
        self.tts_MessageText = ""

        # iot相关变量
        self.iot_descriptors = {}
        self.func_handler = None

        self.cmd_exit = self.config["exit_commands"]
        self.max_cmd_length = 0
        for cmd in self.cmd_exit:
            if len(cmd) > self.max_cmd_length:
                self.max_cmd_length = len(cmd)

        # 是否在聊天结束后关闭连接
        self.close_after_chat = False
        self.load_function_plugin = False
        self.intent_type = "nointent"

        self.timeout_seconds = (
            int(self.config.get("close_connection_no_voice_time", 120)) + 60
        )  # 在原来第一道关闭的基础上加60秒，进行二道关闭
        self.timeout_task = None

        # {"mcp":true} 表示启用MCP功能
        self.features = None

        # 初始化提示词管理器
        self.prompt_manager = PromptManager(config, self.logger)

        # 初始化场景教学处理器
        self.teaching_handler = TeachingHandler(self)
        
        # 添加儿童姓名属性
        self.child_name = "小朋友"

    async def handle_connection(self, ws):
        self._closed = False  # 初始化关闭标志
        try:
            # 获取并验证headers
            self.headers = dict(ws.request.headers)

            if self.headers.get("device-id", None) is None:
                # 尝试从 URL 的查询参数中获取 device-id
                from urllib.parse import parse_qs, urlparse

                # 从 WebSocket 请求中获取路径
                request_path = ws.request.path
                if not request_path:
                    self.logger.bind(tag=TAG).error("无法获取请求路径")
                    return
                parsed_url = urlparse(request_path)
                query_params = parse_qs(parsed_url.query)
                if "device-id" in query_params:
                    self.headers["device-id"] = query_params["device-id"][0]
                    self.headers["client-id"] = query_params["client-id"][0]
                else:
                    await ws.send("端口正常，如需测试连接，请使用test_page.html")
                    await self.close(ws)
                    return
            real_ip = self.headers.get("x-real-ip") or self.headers.get(
                "x-forwarded-for"
            )
            if real_ip:
                self.client_ip = real_ip.split(",")[0].strip()
            else:
                self.client_ip = ws.remote_address[0]
            self.logger.bind(tag=TAG).info(
                f"{self.client_ip} conn - Headers: {self.headers}"
            )

            # 进行认证
            await self.auth.authenticate(self.headers)

            # 认证通过,继续处理
            self.websocket = ws
            self.device_id = self.headers.get("device-id", None)

            # 🔥 使用设备ID作为session_id，这样LLM可以识别同一用户
            if self.device_id:
                self.session_id = self.device_id
                self.logger.bind(tag=TAG).info(f"✅ 获得设备ID: {self.device_id}")
                self.logger.bind(tag=TAG).info(f"✅ 使用设备ID作为session_id: {self.session_id}")
            else:
                self.logger.bind(tag=TAG).warning("❌ 未获取到设备ID，使用随机session_id")
                self.logger.bind(tag=TAG).warning(f"🎲 随机session_id: {self.session_id}")

            # 🔥 新建连接时清除Redis状态，确保新连接不受之前状态影响
            await self._clear_redis_state_on_new_connection()


            # 初始化活动时间戳
            self.last_activity_time = time.time() * 1000

            # 启动超时检查任务
            self.timeout_task = asyncio.create_task(self._check_timeout())

            self.welcome_msg = self.config["xiaozhi"]
            self.welcome_msg["session_id"] = self.session_id

            # 获取差异化配置
            self._initialize_private_config()
            # 立即初始化组件（包括TTS）
            #            # 异步初始化
            self.executor.submit(self._initialize_components)

            # 等待TTS初始化完成后发送欢迎语音
            await self._send_welcome_voice()

            try:
                async for message in self.websocket:
                    await self._route_message(message)
            except websockets.exceptions.ConnectionClosed:
                self.logger.bind(tag=TAG).info("客户端断开连接")

        except AuthenticationError as e:
            self.logger.bind(tag=TAG).error(f"Authentication failed: {str(e)}")
            return
        except Exception as e:
            stack_trace = traceback.format_exc()
            self.logger.bind(tag=TAG).error(f"Connection error: {str(e)}-{stack_trace}")
            return
        finally:
            try:
                await self._save_and_close(ws)
            except Exception as final_error:
                self.logger.bind(tag=TAG).error(f"最终清理时出错: {final_error}")
                # 确保即使保存记忆失败，也要关闭连接
                try:
                    await self.close(ws)
                except Exception as close_error:
                    self.logger.bind(tag=TAG).error(
                        f"强制关闭连接时出错: {close_error}"
                    )

    async def _save_and_close(self, ws):
        """保存记忆并关闭连接"""
        try:
            if self.memory:
                # 使用线程池异步保存记忆
                def save_memory_task():
                    try:
                        # 创建新事件循环（避免与主循环冲突）
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            self.memory.save_memory(self.dialogue.dialogue)
                        )
                    except Exception as e:
                        self.logger.bind(tag=TAG).error(f"保存记忆失败: {e}")
                    finally:
                        try:
                            loop.close()
                        except Exception:
                            pass

                # 启动线程保存记忆，不等待完成
                threading.Thread(target=save_memory_task, daemon=True).start()
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"保存记忆失败: {e}")
        finally:
            # 立即关闭连接，不等待记忆保存完成
            try:
                await self.close(ws)
            except Exception as close_error:
                self.logger.bind(tag=TAG).error(
                    f"保存记忆后关闭连接失败: {close_error}"
                )

    async def _route_message(self, message):
        """消息路由"""
        if isinstance(message, str):
            await handleTextMessage(self, message)
        elif isinstance(message, bytes):
            if self.vad is None:
                return
            if self.asr is None:
                return
            self.asr_audio_queue.put(message)

    async def handle_restart(self, message):
        """处理服务器重启请求"""
        try:

            self.logger.bind(tag=TAG).info("收到服务器重启指令，准备执行...")

            # 发送确认响应
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "success",
                        "message": "服务器重启中...",
                        "content": {"action": "restart"},
                    }
                )
            )

            # 异步执行重启操作
            def restart_server():
                """实际执行重启的方法"""
                time.sleep(1)
                self.logger.bind(tag=TAG).info("执行服务器重启...")
                subprocess.Popen(
                    [sys.executable, "app.py"],
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                    start_new_session=True,
                )
                os._exit(0)

            # 使用线程执行重启避免阻塞事件循环
            threading.Thread(target=restart_server, daemon=True).start()

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"重启失败: {str(e)}")
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "server",
                        "status": "error",
                        "message": f"Restart failed: {str(e)}",
                        "content": {"action": "restart"},
                    }
                )
            )

    def _initialize_components(self):
        try:
            self.selected_module_str = build_module_string(
                self.config.get("selected_module", {})
            )
            self.logger = create_connection_logger(self.selected_module_str)

            """初始化组件"""
            if self.config.get("prompt") is not None:
                user_prompt = self.config["prompt"]
                # 使用快速提示词进行初始化
                prompt = self.prompt_manager.get_quick_prompt(user_prompt)
                self.change_system_prompt(prompt)
                self.logger.bind(tag=TAG).info(
                    f"快速初始化组件: prompt成功 {prompt[:50]}..."
                )

            """初始化本地组件"""
            if self.vad is None:
                self.vad = self._vad
            if self.asr is None:
                self.asr = self._initialize_asr()
            # 初始化声纹识别
            self._initialize_voiceprint()
            # 打开语音识别通道
            asyncio.run_coroutine_threadsafe(
                self.asr.open_audio_channels(self), self.loop
            )
            # 立即初始化TTS并确保完全就绪
            # 立即初始化TTS并确保完全就绪
            if self.tts is None:
                self.tts = self._initialize_tts()

            # 打开语音合成通道
            asyncio.run_coroutine_threadsafe(
                self.tts.open_audio_channels(self), self.loop
            )
            
            # 新增：打印 TTS、ASR、VAD 初始化情况
            self.logger.bind(tag=TAG).info(f"TTS 实例: {self.tts}, 类型: {type(self.tts)}")
            self.logger.bind(tag=TAG).info(f"ASR 实例: {self.asr}, 类型: {type(self.asr)}")
            self.logger.bind(tag=TAG).info(f"VAD 实例: {self.vad}, 类型: {type(self.vad)}")

            """加载记忆"""
            self._initialize_memory()
            """加载意图识别"""
            self._initialize_intent()
            """初始化上报线程"""
            self._init_report_threads()
            """更新系统提示词"""
            self._init_prompt_enhancement()

            # 新增：打印 LLM 初始化情况
            self.logger.bind(tag=TAG).info(f"LLM 实例: {self.llm}, 类型: {type(self.llm)}")

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"实例化组件失败: {e}")

    def _init_prompt_enhancement(self):
        # 更新上下文信息
        self.prompt_manager.update_context_info(self, self.client_ip)
        enhanced_prompt = self.prompt_manager.build_enhanced_prompt(
            self.config["prompt"], self.device_id, self.client_ip
        )
        if enhanced_prompt:
            self.change_system_prompt(enhanced_prompt)
            self.logger.bind(tag=TAG).info("系统提示词已增强更新")

    def _init_report_threads(self):
        """初始化ASR和TTS上报线程"""
        if not self.read_config_from_api or self.need_bind:
            return
        if self.chat_history_conf == 0:
            return
        if self.report_thread is None or not self.report_thread.is_alive():
            self.report_thread = threading.Thread(
                target=self._report_worker, daemon=True
            )
            self.report_thread.start()
            self.logger.bind(tag=TAG).info("TTS上报线程已启动")

    def _initialize_tts(self):
        """初始化TTS"""
        tts = None


        if not self.need_bind:
            try:
                self.logger.bind(tag=TAG).info("开始初始化TTS服务...")
                tts = initialize_tts(self.config)
                if tts is not None:
                    self.logger.bind(tag=TAG).info(f"TTS服务初始化成功: {type(tts).__name__}")
                else:
                    self.logger.bind(tag=TAG).warning("TTS服务初始化返回None，将使用DefaultTTS")
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"TTS服务初始化失败: {str(e)}")
                self.logger.bind(tag=TAG).error(f"异常类型: {type(e).__name__}")
                import traceback
                self.logger.bind(tag=TAG).error(f"异常堆栈: {traceback.format_exc()}")
                tts = None

        if tts is None:
            self.logger.bind(tag=TAG).warning("使用DefaultTTS作为备选方案")
            tts = DefaultTTS(self.config, delete_audio_file=True)

        return tts

    def _initialize_tts_complete(self):
        """完整初始化TTS并确保就绪"""
        try:
            if self.tts is None:
                self.logger.bind(tag=TAG).info("开始初始化TTS...")
                self.tts = self._initialize_tts()
                self.logger.bind(tag=TAG).info(f"TTS实例创建完成: {type(self.tts).__name__}")
            
                            # 确保TTS音频通道已打开
                if not hasattr(self.tts, 'conn') or self.tts.conn is None:
                    self.logger.bind(tag=TAG).info("开始打开TTS音频通道...")
                    try:
                        # 使用同步方式等待TTS音频通道打开
                        future = asyncio.run_coroutine_threadsafe(
                            self.tts.open_audio_channels(self), self.loop
                        )
                        # 等待异步操作完成，最多等待5秒
                        future.result(timeout=5)
                        self.logger.bind(tag=TAG).info("TTS音频通道已打开")
                        
                    except Exception as e:
                        self.logger.bind(tag=TAG).warning(f"TTS音频通道打开失败: {e}")
                        # 即使音频通道打开失败，也继续使用TTS实例
                        self.logger.bind(tag=TAG).info("继续使用TTS实例，音频通道将在需要时重新初始化")
            else:
                self.logger.bind(tag=TAG).info("TTS音频通道已存在")
                
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"TTS完整初始化失败: {e}")

    def _wait_tts_threads_ready(self):
        """等待TTS线程启动就绪"""
        max_wait_time = 10  # 最多等待10秒
        wait_count = 0
        
        while wait_count < max_wait_time:
            try:
                # 检查TTS文本处理线程是否已启动
                if (hasattr(self.tts, 'tts_priority_thread') and 
                    self.tts.tts_priority_thread.is_alive()):
                    self.logger.bind(tag=TAG).info("TTS文本处理线程已就绪")
                    
                    # 检查TTS音频播放线程是否已启动
                    if (hasattr(self.tts, 'audio_play_priority_thread') and 
                        self.tts.audio_play_priority_thread.is_alive()):
                        self.logger.bind(tag=TAG).info("TTS音频播放线程已就绪")
                        self.logger.bind(tag=TAG).info("TTS完全初始化完成")
                        return True
                    else:
                        self.logger.bind(tag=TAG).info(f"等待TTS音频播放线程启动... ({wait_count + 1}/{max_wait_time})")
                else:
                    self.logger.bind(tag=TAG).info(f"等待TTS文本处理线程启动... ({wait_count + 1}/{max_wait_time})")
                    
            except Exception as e:
                self.logger.bind(tag=TAG).warning(f"检查TTS线程状态时出错: {e}")
            
            time.sleep(1)
            wait_count += 1
        
        self.logger.bind(tag=TAG).warning("TTS线程启动超时，但继续使用")
        return False

    async def _send_welcome_voice(self):
        """发送欢迎语音，询问用户名字"""
        try:
            # 如果是刚被唤醒，等待6秒让唤醒词播放完成
            # if hasattr(self, 'just_woken_up') and self.just_woken_up:
            #     self.logger.bind(tag=TAG).info("检测到唤醒状态，等待唤醒词播放完成(6秒)...")
            #     await asyncio.sleep(6)  # 固定等待6秒
            #     self.just_woken_up = False
            #     self.logger.bind(tag=TAG).info("唤醒词播放完成，继续欢迎流程")

            # 等待TTS初始化完成
            self.logger.bind(tag=TAG).info("等待TTS初始化完成...")
            max_wait_time = 15  # 最多等待15秒
            wait_count = 0
            
            while wait_count < max_wait_time:
                if (hasattr(self, 'tts') and self.tts is not None and
                    hasattr(self.tts, 'tts_priority_thread') and 
                    self.tts.tts_priority_thread.is_alive() and
                    hasattr(self.tts, 'audio_play_priority_thread') and 
                    self.tts.audio_play_priority_thread.is_alive()):
                    self.logger.bind(tag=TAG).info("TTS初始化完成，开始发送欢迎语音")
                    break
                
                await asyncio.sleep(1)
                wait_count += 1
                self.logger.bind(tag=TAG).info(f"等待TTS初始化... ({wait_count}/{max_wait_time})")
            
            if wait_count >= max_wait_time:
                self.logger.bind(tag=TAG).warning("TTS初始化超时，跳过欢迎语音")
                return
            
            # 检查用户是否已有姓名
            from core.providers.user.user_info_manager import UserInfoManager
            user_manager = UserInfoManager(self.config)
            
            try:
                has_name = user_manager.has_user_name(self.device_id)
                
                if not has_name:
                    # 用户没有姓名，询问姓名
                    welcome_message = "请问你叫什么名字呢？"
                    self.logger.bind(tag=TAG).info(f"用户 {self.device_id} 没有姓名，发送欢迎语音询问姓名")
                    
                    # 尝试记录交互（如果API不可用则忽略）
                    try:
                        user_manager.record_interaction(self.device_id, "greeting", "", welcome_message)
                    except Exception as record_error:
                        self.logger.bind(tag=TAG).warning(f"记录交互失败，但继续发送欢迎语音: {record_error}")
                    
                    # 发送TTS语音
                    self.tts.tts_one_sentence(self, ContentType.TEXT, content_detail=welcome_message)
                else:
                    # 用户已有姓名，获取用户信息
                    user_info = user_manager.get_user_info(self.device_id)
                    user_name = user_info.get("userName") if user_info else "朋友"
                    
                    welcome_message = f"你好 {user_name}！很高兴再次见到你！有什么我可以帮助你的吗？"
                    self.logger.bind(tag=TAG).info(f"用户 {self.device_id} 已有姓名: {user_name}")
                    
                    # 尝试记录交互（如果API不可用则忽略）
                    try:
                        user_manager.record_interaction(self.device_id, "greeting", "", welcome_message)
                    except Exception as record_error:
                        self.logger.bind(tag=TAG).warning(f"记录交互失败，但继续发送欢迎语音: {record_error}")
                    
                    # 发送TTS语音
                    self.tts.tts_one_sentence(self, ContentType.TEXT, content_detail=welcome_message)
                    
            except Exception as api_error:
                # API调用失败，发送通用欢迎语音
                self.logger.bind(tag=TAG).warning(f"用户信息API调用失败，发送通用欢迎语音: {api_error}")
                welcome_message = "你好！我是小智，很高兴认识你！有什么我可以帮助你的吗？"
                self.tts.tts_one_sentence(self, ContentType.TEXT, content_detail=welcome_message)
                
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"发送欢迎语音失败: {e}")
            import traceback
            self.logger.bind(tag=TAG).error(f"异常堆栈: {traceback.format_exc()}")

    def _initialize_asr(self):
        """初始化ASR"""
        if self._asr.interface_type == InterfaceType.LOCAL:
            # 如果公共ASR是本地服务，则直接返回
            # 因为本地一个实例ASR，可以被多个连接共享
            asr = self._asr
        else:
            # 如果公共ASR是远程服务，则初始化一个新实例
            # 因为远程ASR，涉及到websocket连接和接收线程，需要每个连接一个实例
            asr = initialize_asr(self.config)

        return asr

    def _initialize_voiceprint(self):
        """为当前连接初始化声纹识别"""
        try:
            voiceprint_config = self.config.get("voiceprint", {})
            if voiceprint_config:
                self.voiceprint_provider = VoiceprintProvider(voiceprint_config)
                self.logger.bind(tag=TAG).info("声纹识别功能已在连接时动态启用")
            else:
                self.logger.bind(tag=TAG).info("声纹识别功能未启用或配置不完整")
        except Exception as e:
            self.logger.bind(tag=TAG).warning(f"声纹识别初始化失败: {str(e)}")

    def _initialize_private_config(self):
        """如果是从配置文件获取，则进行二次实例化"""
        if not self.read_config_from_api:
            self.logger.info("[TTS调试] read_config_from_api=False，跳过差异化配置拉取")
            return
        """从接口获取差异化的配置进行二次实例化，非全量重新实例化"""
        try:
            begin_time = time.time()
            private_config = get_private_config_from_api(
                self.config,
                self.headers.get("device-id"),
                self.headers.get("client-id", self.headers.get("device-id")),
            )
            private_config["delete_audio"] = bool(self.config.get("delete_audio", True))
            self.logger.info(f"[TTS调试] {time.time() - begin_time} 秒，获取差异化配置成功: {json.dumps(filter_sensitive_info(private_config), ensure_ascii=False)}")
        except DeviceNotFoundException as e:
            self.need_bind = True
            private_config = {}
            self.logger.warning(f"[TTS调试] DeviceNotFoundException, need_bind=True")
        except DeviceBindException as e:
            self.need_bind = True
            self.bind_code = e.bind_code
            private_config = {}
            self.logger.warning(f"[TTS调试] DeviceBindException, need_bind=True, bind_code={self.bind_code}")
        except Exception as e:
            self.need_bind = True
            self.logger.error(f"[TTS调试] 获取差异化配置失败: {e}")
            private_config = {}

        init_llm, init_tts, init_memory, init_intent = (
            False,
            False,
            False,
            False,
        )

        init_vad = check_vad_update(self.common_config, private_config)
        init_asr = check_asr_update(self.common_config, private_config)

        if init_vad:
            self.config["VAD"] = private_config["VAD"]
            self.config["selected_module"]["VAD"] = private_config["selected_module"]["VAD"]
        if init_asr:
            self.config["ASR"] = private_config["ASR"]
            self.config["selected_module"]["ASR"] = private_config["selected_module"]["ASR"]
        if private_config.get("TTS", None) is not None:
            init_tts = True
            self.config["TTS"] = private_config["TTS"]
            self.config["selected_module"]["TTS"] = private_config["selected_module"]["TTS"]
            self.logger.info(f"[TTS调试] 检测到TTS差异化配置，init_tts={init_tts}, TTS配置: {json.dumps(self.config['TTS'], ensure_ascii=False)}")
        if private_config.get("LLM", None) is not None:
            init_llm = True
            self.config["LLM"] = private_config["LLM"]
            self.config["selected_module"]["LLM"] = private_config["selected_module"]["LLM"]

        self.logger.info(f"[TTS调试] 差异化配置流程结束, init_tts={init_tts}, need_bind={self.need_bind}")

        if private_config.get("VLLM", None) is not None:
            self.config["VLLM"] = private_config["VLLM"]
            self.config["selected_module"]["VLLM"] = private_config["selected_module"][
                "VLLM"
            ]
        if private_config.get("Memory", None) is not None:
            init_memory = True
            self.config["Memory"] = private_config["Memory"]
            self.config["selected_module"]["Memory"] = private_config[
                "selected_module"
            ]["Memory"]
        if private_config.get("Intent", None) is not None:
            init_intent = True
            self.config["Intent"] = private_config["Intent"]
            model_intent = private_config.get("selected_module", {}).get("Intent", {})
            self.config["selected_module"]["Intent"] = model_intent
            # 加载插件配置
            if model_intent != "Intent_nointent":
                plugin_from_server = private_config.get("plugins", {})
                for plugin, config_str in plugin_from_server.items():
                    plugin_from_server[plugin] = json.loads(config_str)
                self.config["plugins"] = plugin_from_server
                self.config["Intent"][self.config["selected_module"]["Intent"]][
                    "functions"
                ] = plugin_from_server.keys()
        if private_config.get("prompt", None) is not None:
            self.config["prompt"] = private_config["prompt"]
        # 获取声纹信息
        if private_config.get("voiceprint", None) is not None:
            self.config["voiceprint"] = private_config["voiceprint"]
        if private_config.get("summaryMemory", None) is not None:
            self.config["summaryMemory"] = private_config["summaryMemory"]
        if private_config.get("device_max_output_size", None) is not None:
            self.max_output_size = int(private_config["device_max_output_size"])
        if private_config.get("chat_history_conf", None) is not None:
            self.chat_history_conf = int(private_config["chat_history_conf"])
        if private_config.get("mcp_endpoint", None) is not None:
            self.config["mcp_endpoint"] = private_config["mcp_endpoint"]
        try:
            modules = initialize_modules(
                self.logger,
                private_config,
                init_vad,
                init_asr,
                init_llm,
                init_tts,
                init_memory,
                init_intent,
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"初始化组件失败: {e}")
            modules = {}
        if modules.get("tts", None) is not None:
            self.tts = modules["tts"]
            self.logger.info(f"[TTS调试] self.tts 被赋值于配置初始化阶段: {self.tts}, type: {type(self.tts)}, conn: {getattr(self.tts, 'conn', None)}, tts_priority_thread: {getattr(self.tts, 'tts_priority_thread', None)}")
        if modules.get("vad", None) is not None:
            self.vad = modules["vad"]
        if modules.get("asr", None) is not None:
            self.asr = modules["asr"]
        if modules.get("llm", None) is not None:
            self.llm = modules["llm"]
        # 新增：打印各模块初始化情况
        self.logger.bind(tag=TAG).info(f"[modules] TTS: {self.tts}, type: {type(self.tts)}")
        self.logger.info(f"[TTS调试] [modules] TTS.conn: {getattr(self.tts, 'conn', None)}, tts_priority_thread: {getattr(self.tts, 'tts_priority_thread', None)}")
        self.logger.bind(tag=TAG).info(f"[modules] VAD: {self.vad}, type: {type(self.vad)}")
        self.logger.bind(tag=TAG).info(f"[modules] ASR: {self.asr}, type: {type(self.asr)}")
        self.logger.bind(tag=TAG).info(f"[modules] LLM: {self.llm}, type: {type(self.llm)}")
        if modules.get("intent", None) is not None:
            self.intent = modules["intent"]
        if modules.get("memory", None) is not None:
            self.memory = modules["memory"]

    def _initialize_memory(self):
        if self.memory is None:
            return
        """初始化记忆模块"""
        self.memory.init_memory(
            role_id=self.device_id,
            llm=self.llm,
            summary_memory=self.config.get("summaryMemory", None),
            save_to_file=not self.read_config_from_api,
        )

        # 获取记忆总结配置
        memory_config = self.config["Memory"]
        memory_type = self.config["Memory"][self.config["selected_module"]["Memory"]][
            "type"
        ]
        # 如果使用 nomen，直接返回
        if memory_type == "nomem":
            return
        # 使用 mem_local_short 模式
        elif memory_type == "mem_local_short":
            memory_llm_name = memory_config[self.config["selected_module"]["Memory"]][
                "llm"
            ]
            if memory_llm_name and memory_llm_name in self.config["LLM"]:
                # 如果配置了专用LLM，则创建独立的LLM实例
                from core.utils import llm as llm_utils

                memory_llm_config = self.config["LLM"][memory_llm_name]
                memory_llm_type = memory_llm_config.get("type", memory_llm_name)
                memory_llm = llm_utils.create_instance(
                    memory_llm_type, memory_llm_config
                )
                self.logger.bind(tag=TAG).info(
                    f"为记忆总结创建了专用LLM: {memory_llm_name}, 类型: {memory_llm_type}"
                )
                self.memory.set_llm(memory_llm)
            else:
                # 否则使用主LLM
                self.memory.set_llm(self.llm)
                self.logger.bind(tag=TAG).info("使用主LLM作为意图识别模型")

    def _initialize_intent(self):
        if self.intent is None:
            return
        self.intent_type = self.config["Intent"][
            self.config["selected_module"]["Intent"]
        ]["type"]
        if self.intent_type == "function_call" or self.intent_type == "intent_llm":
            self.load_function_plugin = True
        """初始化意图识别模块"""
        # 获取意图识别配置
        intent_config = self.config["Intent"]
        intent_type = self.config["Intent"][self.config["selected_module"]["Intent"]][
            "type"
        ]

        # 如果使用 nointent，直接返回
        if intent_type == "nointent":
            return
        # 使用 intent_llm 模式
        elif intent_type == "intent_llm":
            intent_llm_name = intent_config[self.config["selected_module"]["Intent"]][
                "llm"
            ]

            if intent_llm_name and intent_llm_name in self.config["LLM"]:
                # 如果配置了专用LLM，则创建独立的LLM实例
                from core.utils import llm as llm_utils

                intent_llm_config = self.config["LLM"][intent_llm_name]
                intent_llm_type = intent_llm_config.get("type", intent_llm_name)
                intent_llm = llm_utils.create_instance(
                    intent_llm_type, intent_llm_config
                )
                self.logger.bind(tag=TAG).info(
                    f"为意图识别创建了专用LLM: {intent_llm_name}, 类型: {intent_llm_type}"
                )
                self.intent.set_llm(intent_llm)
            else:
                # 否则使用主LLM
                self.intent.set_llm(self.llm)
                self.logger.bind(tag=TAG).info("使用主LLM作为意图识别模型")

        """加载统一工具处理器"""
        self.func_handler = UnifiedToolHandler(self)

        # 异步初始化工具处理器
        if hasattr(self, "loop") and self.loop:
            asyncio.run_coroutine_threadsafe(self.func_handler._initialize(), self.loop)

    def change_system_prompt(self, prompt):
        self.prompt = prompt
        # 更新系统prompt至上下文
        self.dialogue.update_system_message(self.prompt)


    def _handle_chat_mode(self, query):
        """处理聊天模式切换和教学模式逻辑"""
        return self.teaching_handler.handle_chat_mode(query)





    def chat(self, query, tool_call=False, depth=0):
        self.logger.bind(tag=TAG).info(f"大模型收到用户消息: {query}")
        # 打印当前 LLM 实例类型和 LLM 配置
        self.logger.bind(tag=TAG).info(f"当前 LLM 实例: {type(self.llm)}")
        self.logger.bind(tag=TAG).info(f"当前 LLM 配置: {self.config.get('LLM')}")
        self.logger.bind(tag=TAG).info(f"当前选中 LLM: {self.config.get('selected_module', {}).get('LLM')}")
        self.llm_finish_task = False
        depth = 0
        
        # 用户信息检查已移至连接时处理，此处不再检查
        
        # 检查聊天模式（只在最顶层调用时检查）
        if depth == 0:
            chat_result = self._handle_chat_mode(query)
            if chat_result:
                return chat_result

        if not tool_call:
            self.dialogue.put(Message(role="user", content=query))

        # 为最顶层时新建会话ID和发送FIRST请求
        if depth == 0:
            self.sentence_id = str(uuid.uuid4().hex)
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.FIRST,
                    content_type=ContentType.ACTION,
                )
            )

        # Define intent functions
        functions = None
        if self.intent_type == "function_call" and hasattr(self, "func_handler"):
            functions = self.func_handler.get_functions()
        response_message = []

        try:
            # 使用带记忆的对话
            memory_str = None
            if self.memory is not None:
                future = asyncio.run_coroutine_threadsafe(
                    self.memory.query_memory(query), self.loop
                )
                memory_str = future.result()

            if self.intent_type == "function_call" and functions is not None:
                self.logger.bind(tag=TAG).info("调用 LLM response_with_functions ...")
                llm_responses = self.llm.response_with_functions(
                    self.session_id,
                    self.dialogue.get_llm_dialogue_with_memory(
                        memory_str, self.config.get("voiceprint", {})
                    ),
                    functions=functions,
                )
            else:
                self.logger.bind(tag=TAG).info("调用 LLM response ...")
                llm_responses = self.llm.response(
                    self.session_id,
                    self.dialogue.get_llm_dialogue_with_memory(
                        memory_str, self.config.get("voiceprint", {})
                    ),
                )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"LLM 处理出错 {query}: {e}")
            return None

        # 处理流式响应
        tool_call_flag = False
        function_name = None
        function_id = None
        function_arguments = ""
        content_arguments = ""
        self.client_abort = False
        emotion_flag = True
        for response in llm_responses:

            # self.logger.info(f"[LLM消费] 收到response: {response}")

            
            if self.client_abort:
                break
            if self.intent_type == "function_call" and functions is not None:
                # 检查response是否是元组（正常情况）还是字符串（错误情况）
                if isinstance(response, tuple):
                    content, tools_call = response
                elif isinstance(response, dict) and "content" in response:
                    content = response["content"]
                    tools_call = None
                else:
                    # 处理错误情况，response是字符串
                    content = response
                    tools_call = None
                if content is not None and len(content) > 0:
                    content_arguments += content

                if not tool_call_flag and content_arguments.startswith("<tool_call>"):
                    # print("content_arguments", content_arguments)
                    tool_call_flag = True

                if tools_call is not None and len(tools_call) > 0:
                    tool_call_flag = True
                    if tools_call[0].id is not None:
                        function_id = tools_call[0].id
                    if tools_call[0].function.name is not None:
                        function_name = tools_call[0].function.name
                    if tools_call[0].function.arguments is not None:
                        function_arguments += tools_call[0].function.arguments
            else:
                content = response

            # 在llm回复中获取情绪表情，一轮对话只在开头获取一次
            if emotion_flag and content is not None and content.strip():
                asyncio.run_coroutine_threadsafe(
                    textUtils.get_emotion(self, content),
                    self.loop,
                )
                emotion_flag = False


            # 在推送到TTS队列前，先打印TTS实例和队列状态
            # self.logger.info(
            #     f"[TTS调试] chat前 self.tts: {self.tts}, conn: {getattr(self.tts, 'conn', None)}, tts_text_queue: {getattr(self.tts, 'tts_text_queue', None)}"
            # )


            if content is not None and len(content) > 0:
                if not tool_call_flag:
                    response_message.append(content)
                    self.tts.tts_text_queue.put(
                        TTSMessageDTO(
                            sentence_id=self.sentence_id,
                            sentence_type=SentenceType.MIDDLE,
                            content_type=ContentType.TEXT,
                            content_detail=content,
                        )
                    )
        # 处理function call
        if tool_call_flag:
            bHasError = False
            if function_id is None:
                a = extract_json_from_string(content_arguments)
                if a is not None:
                    try:
                        content_arguments_json = json.loads(a)
                        function_name = content_arguments_json["name"]
                        function_arguments = json.dumps(
                            content_arguments_json["arguments"], ensure_ascii=False
                        )
                        function_id = str(uuid.uuid4().hex)
                    except Exception as e:
                        bHasError = True
                        response_message.append(a)
                else:
                    bHasError = True
                    response_message.append(content_arguments)
                if bHasError:
                    self.logger.bind(tag=TAG).error(
                        f"function call error: {content_arguments}"
                    )
            if not bHasError:
                # 如需要大模型先处理一轮，添加相关处理后的日志情况
                if len(response_message) > 0:
                    text_buff = "".join(response_message)
                    self.tts_MessageText = text_buff
                    self.dialogue.put(Message(role="assistant", content=text_buff))
                response_message.clear()
                self.logger.bind(tag=TAG).debug(
                    f"function_name={function_name}, function_id={function_id}, function_arguments={function_arguments}"
                )
                function_call_data = {
                    "name": function_name,
                    "id": function_id,
                    "arguments": function_arguments,
                }

                # 使用统一工具处理器处理所有工具调用
                result = asyncio.run_coroutine_threadsafe(
                    self.func_handler.handle_llm_function_call(
                        self, function_call_data
                    ),
                    self.loop,
                ).result()
                self._handle_function_result(result, function_call_data, depth=depth)

        # 存储对话内容
        if len(response_message) > 0:
            text_buff = "".join(response_message)
            self.tts_MessageText = text_buff
            self.dialogue.put(Message(role="assistant", content=text_buff))
        if depth == 0:
            self.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=self.sentence_id,
                    sentence_type=SentenceType.LAST,
                    content_type=ContentType.ACTION,
                )
            )
        self.llm_finish_task = True
        # 使用lambda延迟计算，只有在DEBUG级别时才执行get_llm_dialogue()
        self.logger.bind(tag=TAG).debug(
            lambda: json.dumps(
                self.dialogue.get_llm_dialogue(), indent=4, ensure_ascii=False
            )
        )

        return True

    def _handle_function_result(self, result, function_call_data, depth):
        if result.action == Action.RESPONSE:  # 直接回复前端
            text = result.response
            self.tts.tts_one_sentence(self, ContentType.TEXT, content_detail=text)
            self.dialogue.put(Message(role="assistant", content=text))
        elif result.action == Action.REQLLM:  # 调用函数后再请求llm生成回复
            text = result.result
            if text is not None and len(text) > 0:
                function_id = function_call_data["id"]
                function_name = function_call_data["name"]
                function_arguments = function_call_data["arguments"]
                self.dialogue.put(
                    Message(
                        role="assistant",
                        tool_calls=[
                            {
                                "id": function_id,
                                "function": {
                                    "arguments": "{}" if function_arguments == "" else function_arguments,
                                    "name": function_name,
                                },
                                "type": "function",
                                "index": 0,
                            }
                        ],
                    )
                )

                self.dialogue.put(
                    Message(
                        role="tool",
                        tool_call_id=(
                            str(uuid.uuid4()) if function_id is None else function_id
                        ),
                        content=text,
                    )
                )
                self.chat(text, tool_call=True, depth=depth + 1)
        elif result.action == Action.NOTFOUND or result.action == Action.ERROR:
            text = result.response if result.response else result.result
            self.tts.tts_one_sentence(self, ContentType.TEXT, content_detail=text)
            self.dialogue.put(Message(role="assistant", content=text))
        else:
            pass

    def _report_worker(self):
        """聊天记录上报工作线程"""
        while not self.stop_event.is_set():
            try:
                # 从队列获取数据，设置超时以便定期检查停止事件
                item = self.report_queue.get(timeout=1)
                if item is None:  # 检测毒丸对象
                    break
                try:
                    # 检查线程池状态
                    if self.executor is None:
                        continue
                    # 提交任务到线程池
                    self.executor.submit(self._process_report, *item)
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"聊天记录上报线程异常: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"聊天记录上报工作线程异常: {e}")

        self.logger.bind(tag=TAG).info("聊天记录上报线程已退出")

    def _process_report(self, type, text, audio_data, report_time):
        """处理上报任务"""
        try:
            # 执行上报（传入二进制数据）
            report(self, type, text, audio_data, report_time)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"上报处理异常: {e}")
        finally:
            # 标记任务完成
            self.report_queue.task_done()

    def clearSpeakStatus(self):
        self.client_is_speaking = False
        self.logger.bind(tag=TAG).debug(f"清除服务端讲话状态")

    async def close(self, ws=None):
        """资源清理方法"""
        if hasattr(self, '_closed') and self._closed:
            return  # 如果已经关闭，直接返回
            
        try:
            # 取消超时任务
            if self.timeout_task and not self.timeout_task.done():
                self.timeout_task.cancel()
                try:
                    await self.timeout_task
                except asyncio.CancelledError:
                    pass
                self.timeout_task = None

            # 清理工具处理器资源
            if hasattr(self, "func_handler") and self.func_handler:
                try:
                    await self.func_handler.cleanup()
                except Exception as cleanup_error:
                    self.logger.bind(tag=TAG).error(
                        f"清理工具处理器时出错: {cleanup_error}"
                    )

            # 清理教学处理器资源
            if hasattr(self, "teaching_handler") and self.teaching_handler:
                try:
                    await self.teaching_handler.cleanup()
                except Exception as teaching_cleanup_error:
                    self.logger.bind(tag=TAG).error(
                        f"清理教学处理器资源时出错: {teaching_cleanup_error}"
                    )

            # 触发停止事件
            if self.stop_event:
                self.stop_event.set()

            # 清空任务队列
            self.clear_queues()

            # 关闭WebSocket连接 - 改进Windows兼容性
            try:
                if ws:
                    # 安全地检查WebSocket状态并关闭
                    try:
                        # 检查连接是否已经关闭
                        is_closed = False
                        if hasattr(ws, "closed"):
                            is_closed = ws.closed
                        elif hasattr(ws, "state"):
                            is_closed = ws.state.name == "CLOSED"
                        
                        if not is_closed:
                            # 使用更安全的关闭方式，避免Windows socket错误
                            try:
                                await asyncio.wait_for(ws.close(), timeout=2.0)
                            except (asyncio.TimeoutError, ConnectionResetError, OSError) as close_error:
                                # Windows系统常见的连接重置错误，可以安全忽略
                                self.logger.bind(tag=TAG).debug(f"WebSocket关闭时出现预期错误（可忽略）: {close_error}")
                            except Exception as close_error:
                                self.logger.bind(tag=TAG).warning(f"WebSocket关闭时出现未预期错误: {close_error}")
                    except Exception as check_error:
                        # 检查状态时出错，尝试直接关闭
                        self.logger.bind(tag=TAG).debug(f"检查WebSocket状态时出错: {check_error}")
                        try:
                            await asyncio.wait_for(ws.close(), timeout=1.0)
                        except Exception:
                            pass
                elif self.websocket:
                    try:
                        # 检查连接是否已经关闭
                        is_closed = False
                        if hasattr(self.websocket, "closed"):
                            is_closed = self.websocket.closed
                        elif hasattr(self.websocket, "state"):
                            is_closed = self.websocket.state.name == "CLOSED"
                        
                        if not is_closed:
                            # 使用更安全的关闭方式
                            try:
                                await asyncio.wait_for(self.websocket.close(), timeout=2.0)
                            except (asyncio.TimeoutError, ConnectionResetError, OSError) as close_error:
                                # Windows系统常见的连接重置错误，可以安全忽略
                                self.logger.bind(tag=TAG).debug(f"WebSocket关闭时出现预期错误（可忽略）: {close_error}")
                            except Exception as close_error:
                                self.logger.bind(tag=TAG).warning(f"WebSocket关闭时出现未预期错误: {close_error}")
                    except Exception as check_error:
                        # 检查状态时出错，尝试直接关闭
                        self.logger.bind(tag=TAG).debug(f"检查WebSocket状态时出错: {check_error}")
                        try:
                            await asyncio.wait_for(self.websocket.close(), timeout=1.0)
                        except Exception:
                            pass
            except Exception as ws_error:
                self.logger.bind(tag=TAG).error(f"关闭WebSocket连接时出错: {ws_error}")

            if self.tts:
                await self.tts.close()

            # 最后关闭线程池（避免阻塞）
            if self.executor:
                try:
                    self.executor.shutdown(wait=False)
                except Exception as executor_error:
                    self.logger.bind(tag=TAG).error(
                        f"关闭线程池时出错: {executor_error}"
                    )
                self.executor = None

            self.logger.bind(tag=TAG).info("连接资源已释放")
            self._closed = True  # 标记为已关闭
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"关闭连接时出错: {e}")
        finally:
            # 确保停止事件被设置
            if self.stop_event:
                self.stop_event.set()

    def clear_queues(self):
        """清空所有任务队列"""
        if self.tts:
            self.logger.bind(tag=TAG).debug(
                f"开始清理: TTS队列大小={self.tts.tts_text_queue.qsize()}, 音频队列大小={self.tts.tts_audio_queue.qsize()}"
            )

            # 使用非阻塞方式清空队列
            for q in [
                self.tts.tts_text_queue,
                self.tts.tts_audio_queue,
                self.report_queue,
            ]:
                if not q:
                    continue
                while True:
                    try:
                        q.get_nowait()
                    except queue.Empty:
                        break

            self.logger.bind(tag=TAG).debug(
                f"清理结束: TTS队列大小={self.tts.tts_text_queue.qsize()}, 音频队列大小={self.tts.tts_audio_queue.qsize()}"
            )

    def reset_vad_states(self):
        self.client_audio_buffer = bytearray()
        self.client_have_voice = False
        self.client_voice_stop = False
        self.logger.bind(tag=TAG).debug("VAD states reset.")

    def chat_and_close(self, text):
        """Chat with the user and then close the connection"""
        try:
            # Use the existing chat method
            self.chat(text)

            # After chat is complete, close the connection
            self.close_after_chat = True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Chat and close error: {str(e)}")

    async def _check_timeout(self):
        """检查连接超时"""
        try:
            while not self.stop_event.is_set():
                # 检查是否超时（只有在时间戳已初始化的情况下）
                if self.last_activity_time > 0.0:
                    current_time = time.time() * 1000
                    if (
                        current_time - self.last_activity_time
                        > self.timeout_seconds * 1000
                    ):
                        if not self.stop_event.is_set():
                            self.logger.bind(tag=TAG).info("连接超时，准备关闭")
                            # 设置停止事件，防止重复处理
                            self.stop_event.set()
                            # 使用 try-except 包装关闭操作，确保不会因为异常而阻塞
                            try:
                                await self.close(self.websocket)
                            except Exception as close_error:
                                self.logger.bind(tag=TAG).error(
                                    f"超时关闭连接时出错: {close_error}"
                                )
                        break
                # 每10秒检查一次，避免过于频繁
                await asyncio.sleep(10)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"超时检查任务出错: {e}")
        finally:
            self.logger.bind(tag=TAG).info("超时检查任务已退出")

    async def _clear_redis_state_on_new_connection(self):
        """
        新建连接时清除Redis状态
        
        确保新连接不受之前连接状态的影响，包括：
        - 聊天状态
        - 教学会话数据
        - 其他相关状态
        """
        try:
            self.logger.bind(tag=TAG).info("开始清理Redis状态，为新连接做准备")
            
            # 获取用户ID（优先使用device_id，否则使用session_id）
            user_id = self.device_id if self.device_id else self.session_id
            
            if not user_id:
                self.logger.bind(tag=TAG).warning("无法获取用户ID，跳过Redis状态清理")
                return
            
            self.logger.bind(tag=TAG).info(f"清理用户 {user_id} 的Redis状态")
            
            # 清理聊天状态
            if hasattr(self, 'teaching_handler') and self.teaching_handler:
                try:
                    # 清理聊天状态管理器中的用户状态
                    if hasattr(self.teaching_handler, 'chat_status_manager'):
                        success = self.teaching_handler.chat_status_manager.clear_user_chat_status(user_id)
                        if success:
                            self.logger.bind(tag=TAG).info(f"✅ 成功清理用户 {user_id} 的聊天状态")
                        else:
                            self.logger.bind(tag=TAG).warning(f"⚠️ 用户 {user_id} 的聊天状态不存在或清理失败")
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"清理聊天状态失败: {e}")
            
            # 清理教学会话数据
            try:
                from core.utils.redis_client import get_redis_client
                redis_client = get_redis_client()
                
                # 清理教学会话数据
                session_key = f"teaching_{user_id}"
                session_deleted = redis_client.delete_session_data(session_key)
                if session_deleted:
                    self.logger.bind(tag=TAG).info(f"✅ 成功清理用户 {user_id} 的教学会话数据")
                else:
                    self.logger.bind(tag=TAG).info(f"ℹ️ 用户 {user_id} 没有教学会话数据需要清理")
                
                # 清理聊天状态（双重保险）
                chat_status_deleted = redis_client.delete_chat_status(user_id)
                if chat_status_deleted:
                    self.logger.bind(tag=TAG).info(f"✅ 成功清理用户 {user_id} 的聊天状态")
                else:
                    self.logger.bind(tag=TAG).info(f"ℹ️ 用户 {user_id} 没有聊天状态需要清理")
                    
            except Exception as e:
                self.logger.bind(tag=TAG).error(f"清理Redis数据失败: {e}")
            
            # 重置教学处理器状态
            if hasattr(self, 'teaching_handler') and self.teaching_handler:
                try:
                    # 重置儿童姓名
                    self.teaching_handler.child_name = "小朋友"
                    self.logger.bind(tag=TAG).info("✅ 重置教学处理器状态")
                except Exception as e:
                    self.logger.bind(tag=TAG).error(f"重置教学处理器状态失败: {e}")
            
            self.logger.bind(tag=TAG).info("Redis状态清理完成，新连接已准备就绪")
            
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"清理Redis状态时出错: {e}")
            # 即使清理失败，也不应该阻止连接建立
            self.logger.bind(tag=TAG).warning("继续建立连接，但可能存在状态残留")
