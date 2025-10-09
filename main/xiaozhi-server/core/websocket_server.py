import asyncio
import websockets
import sys
from config.logger import setup_logging
from core.connection import ConnectionHandler
from config.config_loader import get_config_from_api
from core.utils.modules_initialize import initialize_modules
from core.utils.util import check_vad_update, check_asr_update

TAG = __name__


def handle_windows_connection_errors():
    """处理Windows系统特有的连接错误"""
    def exception_handler(loop, context):
        exception = context.get('exception')
        if exception:
            # 捕获Windows系统常见的连接重置错误
            if isinstance(exception, (ConnectionResetError, OSError)):
                if "WinError 10054" in str(exception) or "远程主机强迫关闭" in str(exception):
                    # 这是Windows系统上客户端突然断开连接时的正常现象，可以安全忽略
                    logger = setup_logging()
                    logger.bind(tag=TAG).debug(f"捕获到Windows连接重置错误（可忽略）: {exception}")
                    return
            
            # 其他异常继续正常处理
            loop.default_exception_handler(context)
        else:
            loop.default_exception_handler(context)
    
    # 设置异常处理器
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)


class WebSocketServer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        self.config_lock = asyncio.Lock()
        modules = initialize_modules(
            self.logger,
            self.config,
            "VAD" in self.config["selected_module"],
            "ASR" in self.config["selected_module"],
            "LLM" in self.config["selected_module"],
            False,
            "Memory" in self.config["selected_module"],
            "Intent" in self.config["selected_module"],
        )
        self._vad = modules["vad"] if "vad" in modules else None
        self._asr = modules["asr"] if "asr" in modules else None
        self._llm = modules["llm"] if "llm" in modules else None
        self._intent = modules["intent"] if "intent" in modules else None
        self._memory = modules["memory"] if "memory" in modules else None

        self.active_connections = set()

    async def start(self):
        # 设置Windows连接错误处理器
        handle_windows_connection_errors()
        
        server_config = self.config["server"]
        host = server_config.get("ip", "0.0.0.0")
        port = int(server_config.get("port", 8000))

        # 创建WebSocket服务器，添加CORS支持
        start_server = websockets.serve(
            self._handle_connection, 
            host, 
            port, 
            process_request=self._http_response,
            # 添加额外的CORS支持
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        )
        
        async with start_server:
            await asyncio.Future()

    async def _handle_connection(self, websocket):
        """处理新连接，每次创建独立的ConnectionHandler"""
        # 创建ConnectionHandler时传入当前server实例
        handler = ConnectionHandler(
            self.config,
            self._vad,
            self._asr,
            self._llm,
            self._memory,
            self._intent,
            self,  # 传入server实例
        )
        self.active_connections.add(handler)
        try:
            await handler.handle_connection(websocket)
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"处理连接时出错: {e}")
        finally:
            # 确保从活动连接集合中移除
            self.active_connections.discard(handler)
            # 强制关闭连接（如果还没有关闭的话）- 改进Windows兼容性
            try:
                # 安全地检查WebSocket状态并关闭
                is_closed = False
                if hasattr(websocket, "closed"):
                    is_closed = websocket.closed
                elif hasattr(websocket, "state"):
                    is_closed = websocket.state.name == "CLOSED"
                
                if not is_closed:
                    # 使用更安全的关闭方式，避免Windows socket错误
                    try:
                        await asyncio.wait_for(websocket.close(), timeout=2.0)
                    except (asyncio.TimeoutError, ConnectionResetError, OSError) as close_error:
                        # Windows系统常见的连接重置错误，可以安全忽略
                        self.logger.bind(tag=TAG).debug(f"服务器端WebSocket关闭时出现预期错误（可忽略）: {close_error}")
                    except Exception as close_error:
                        self.logger.bind(tag=TAG).warning(f"服务器端WebSocket关闭时出现未预期错误: {close_error}")
            except Exception as check_error:
                # 检查状态时出错，尝试直接关闭
                self.logger.bind(tag=TAG).debug(f"检查WebSocket状态时出错: {check_error}")
                try:
                    await asyncio.wait_for(websocket.close(), timeout=1.0)
                except Exception:
                    pass

    async def _http_response(self, websocket, request_headers):
        """处理HTTP请求和CORS预检请求"""
        try:
            # 获取请求方法
            method = getattr(request_headers, 'method', 'GET')
            
            # 检查是否为 WebSocket 升级请求
            connection_header = request_headers.headers.get("connection", "").lower()
            upgrade_header = request_headers.headers.get("upgrade", "").lower()
            
            if connection_header == "upgrade" and upgrade_header == "websocket":
                # 如果是 WebSocket 请求，返回 None 允许握手继续
                return None
            
            # 处理CORS预检请求（OPTIONS方法）
            if method == "OPTIONS":
                self.logger.bind(tag=TAG).info("处理CORS预检请求")
                cors_headers = [
                    ("Access-Control-Allow-Origin", "*"),
                    ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                    ("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With"),
                    ("Access-Control-Max-Age", "86400"),
                    ("Content-Length", "0")
                ]
                return websocket.respond(200, "", headers=cors_headers)
            
            # 处理普通 HTTP 请求
            else:
                cors_headers = [
                    ("Access-Control-Allow-Origin", "*"),
                    ("Content-Type", "text/plain; charset=utf-8")
                ]
                return websocket.respond(200, "xiaozhi-server is running\n", headers=cors_headers)
                
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"处理HTTP请求时出错: {e}")
            # 出错时返回简单的响应
            return websocket.respond(500, "Internal Server Error")

    async def update_config(self) -> bool:
        """更新服务器配置并重新初始化组件

        Returns:
            bool: 更新是否成功
        """
        try:
            async with self.config_lock:
                # 重新获取配置
                new_config = get_config_from_api(self.config)
                if new_config is None:
                    self.logger.bind(tag=TAG).error("获取新配置失败")
                    return False
                self.logger.bind(tag=TAG).info(f"获取新配置成功")
                # 检查 VAD 和 ASR 类型是否需要更新
                update_vad = check_vad_update(self.config, new_config)
                update_asr = check_asr_update(self.config, new_config)
                self.logger.bind(tag=TAG).info(
                    f"检查VAD和ASR类型是否需要更新: {update_vad} {update_asr}"
                )
                # 更新配置
                self.config = new_config
                # 重新初始化组件
                modules = initialize_modules(
                    self.logger,
                    new_config,
                    update_vad,
                    update_asr,
                    "LLM" in new_config["selected_module"],
                    False,
                    "Memory" in new_config["selected_module"],
                    "Intent" in new_config["selected_module"],
                )

                # 更新组件实例
                if "vad" in modules:
                    self._vad = modules["vad"]
                if "asr" in modules:
                    self._asr = modules["asr"]
                if "llm" in modules:
                    self._llm = modules["llm"]
                if "intent" in modules:
                    self._intent = modules["intent"]
                if "memory" in modules:
                    self._memory = modules["memory"]
                self.logger.bind(tag=TAG).info(f"更新配置任务执行完毕")
                return True
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"更新服务器配置失败: {str(e)}")
            return False
