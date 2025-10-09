# Windows系统ConnectionResetError修复说明

## 问题描述

在Windows系统上运行小智服务器时，当客户端（如测试页面）突然断开连接时，会出现以下错误：

```
ERROR:asyncio:Exception in callback _ProactorBasePipeTransport._call_connection_lost(None)
handle: <Handle _ProactorBasePipeTransport._call_connection_lost(None)>
Traceback (most recent call last):
  File "C:\Users\Administrator\miniconda3\envs\xiaozhi-server\lib\asyncio\events.py", line 80, in _run
    self._context.run(self._callback, *self._args)
  File "C:\Users\Administrator\miniconda3\envs\xiaozhi-server\lib\asyncio\proactor_events.py", line 165, in _call_connection_lost
    self._sock.shutdown(socket.SHUT_RDWR)
ConnectionResetError: [WinError 10054] 远程主机强迫关闭了一个现有的连接。
```

## 问题原因

1. **Windows socket处理机制**：Windows系统对socket的`shutdown`操作比Linux更严格
2. **客户端异常断开**：当客户端突然关闭浏览器、刷新页面或网络中断时，连接被远程强制关闭
3. **异步清理时序**：多个异步任务同时尝试关闭同一个连接，导致竞态条件
4. **asyncio事件循环**：Windows使用`ProactorEventLoop`，对连接关闭的处理与Linux不同

## 修复方案

### 1. 改进WebSocket连接关闭逻辑

**文件**: `main/xiaozhi-server/core/connection.py`

- 添加连接状态检查，避免重复关闭已关闭的连接
- 使用`asyncio.wait_for`设置超时，避免无限等待
- 专门捕获`ConnectionResetError`和`OSError`，将其视为可忽略的错误
- 改进错误日志级别，将预期的连接重置错误设为debug级别

### 2. 改进WebSocket服务器连接处理

**文件**: `main/xiaozhi-server/core/websocket_server.py`

- 在服务器端也应用相同的安全关闭逻辑
- 添加全局异常处理器，专门处理Windows连接错误
- 设置异常处理器在服务器启动时自动激活

### 3. 添加全局异常处理器

```python
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
```

## 修复效果

1. **消除错误日志**：不再显示`ConnectionResetError`错误信息
2. **提高稳定性**：服务器能够优雅处理客户端异常断开
3. **保持功能**：不影响正常的连接和通信功能
4. **跨平台兼容**：修复不影响Linux系统的正常运行

## 测试验证

创建了连接稳定性测试脚本 `test_connection_stability.py`，可以：

1. 测试多个并发连接的稳定性
2. 测试突然断开连接的情况
3. 统计成功率和消息传输情况
4. 验证修复效果

### 运行测试

```bash
cd main/xiaozhi-server
python test_connection_stability.py
```

## 技术细节

### 关键改进点

1. **连接状态检查**：
   ```python
   is_closed = False
   if hasattr(ws, "closed"):
       is_closed = ws.closed
   elif hasattr(ws, "state"):
       is_closed = ws.state.name == "CLOSED"
   ```

2. **安全关闭**：
   ```python
   try:
       await asyncio.wait_for(ws.close(), timeout=2.0)
   except (asyncio.TimeoutError, ConnectionResetError, OSError) as close_error:
       # Windows系统常见的连接重置错误，可以安全忽略
       logger.bind(tag=TAG).debug(f"WebSocket关闭时出现预期错误（可忽略）: {close_error}")
   ```

3. **异常分类处理**：
   - `ConnectionResetError`：客户端强制断开，可忽略
   - `OSError`：系统级错误，通常可忽略
   - `asyncio.TimeoutError`：关闭超时，可忽略
   - 其他异常：记录警告，需要关注

## 注意事项

1. 这个修复主要针对Windows系统，Linux系统不受影响
2. 修复不会影响正常的连接和通信功能
3. 如果出现其他类型的连接错误，仍会正常记录和报告
4. 建议在生产环境中监控连接稳定性，确保修复效果

## 相关文件

- `main/xiaozhi-server/core/connection.py` - 连接处理器
- `main/xiaozhi-server/core/websocket_server.py` - WebSocket服务器
- `main/xiaozhi-server/test_connection_stability.py` - 稳定性测试脚本
- `main/xiaozhi-server/test/test_page.html` - 测试页面（触发场景）
