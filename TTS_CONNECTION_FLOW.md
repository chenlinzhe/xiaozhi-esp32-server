# TTS 连接建立和关闭流程详解

## 📌 概述

每句话独立建立 TTS 连接的完整流程，包括建立连接、发送内容、关闭连接。

---

## 🔵 1. 建立新连接的语句

### 在 teaching_handler.py 中的语句：

```python
# 第469-481行：生成新的 sentence_id 并发送 FIRST 请求
sentence_id = str(uuid.uuid4().hex)  
self.connection.sentence_id = sentence_id

# 🔥 关键：发送 FIRST 请求（StartSession）
self.connection.tts.tts_text_queue.put(  
    TTSMessageDTO(  
        sentence_id=sentence_id,  
        sentence_type=SentenceType.FIRST,  # ← 这是建立新连接的信号
        content_type=ContentType.ACTION,
        speech_rate=speech_rate,
    )  
)
```

### 实现原理（在 TTS Provider 中）：

当 TTS 文本处理线程收到 `SentenceType.FIRST` 时：

#### 第1步：检测并处理（aliyun_stream.py 第217-247行）
```python
if message.sentence_type == SentenceType.FIRST:
    # 重置中断标志
    self.conn.client_abort = False
    
    # 调用 start_session 方法
    future = asyncio.run_coroutine_threadsafe(
        self.start_session(self.conn.sentence_id),
        loop=self.conn.loop,
    )
    future.result()
```

#### 第2步：建立连接（aliyun_stream.py 第325-370行）
```python
async def start_session(self, session_id):
    # 1. 检查并关闭上一个会话（如果有）
    if self._monitor_task is not None and not self._monitor_task.done():
        await self.close()
    
    # 2. 🔥 建立新的 WebSocket 连接
    await self._ensure_connection()
    
    # 3. 启动监听任务（接收 TTS 音频流）
    self._monitor_task = asyncio.create_task(self._start_monitor_tts_response())
    
    # 4. 发送 StartSynthesis 请求到 TTS 服务器
    start_request = {
        "header": {
            "message_id": self.message_id,
            "task_id": self.conn.sentence_id,
            "namespace": "FlowingSpeechSynthesizer",
            "name": "StartSynthesis",  # ← 启动合成会话
            "appkey": self.appkey,
        },
        "payload": {
            "voice": self.voice,
            "format": self.format,
            "sample_rate": self.sample_rate,
            "volume": self.volume,
            "speech_rate": self.speech_rate,
            "pitch_rate": self.pitch_rate,
            "enable_subtitle": True,
        },
    }
    await self.ws.send(json.dumps(start_request))
    logger.info("会话启动请求已发送")
```

#### 第3步：建立 WebSocket 连接（aliyun_stream.py 第179-207行）
```python
async def _ensure_connection(self):
    if self.ws is None or self.ws.closed:
        # 🔥 实际建立 WebSocket 连接
        url = "wss://nls-gateway.aliyuncs.com/ws/v1"
        self.ws = await websockets.connect(
            url,
            extra_headers={
                "X-NLS-Token": self.token,
            },
            max_size=1000000000,
        )
        logger.info("WebSocket 连接建立成功")
        self.last_active_time = time.time()
```

---

## 🟢 2. 发送文本内容

```python
# 第484-493行：发送 MIDDLE 类型的文本消息
self.connection.tts.tts_text_queue.put(  
    TTSMessageDTO(  
        sentence_id=sentence_id,  
        sentence_type=SentenceType.MIDDLE,  # ← 会话进行中
        content_type=ContentType.TEXT,  
        content_detail=content,  # ← 要合成的文本
        speech_rate=speech_rate,  
    )  
)
```

TTS Provider 会将这段文本通过 WebSocket 发送给 TTS 服务器进行语音合成。

---

## 🔴 3. 结束连接的语句

### 在 teaching_handler.py 中的语句：

```python
# 第496-503行：发送 LAST 请求（结束当前句子的Session）
self.connection.tts.tts_text_queue.put(
    TTSMessageDTO(
        sentence_id=sentence_id,
        sentence_type=SentenceType.LAST,  # ← 这是结束连接的信号
        content_type=ContentType.ACTION,
    )
)
```

### 实现原理（在 TTS Provider 中）：

当 TTS 文本处理线程收到 `SentenceType.LAST` 时：

#### 第1步：检测并处理（aliyun_stream.py 第374-387行 / huoshan_double_stream.py）
```python
if message.sentence_type == SentenceType.LAST:
    try:
        # 调用 finish_session 方法
        future = asyncio.run_coroutine_threadsafe(
            self.finish_session(self.conn.sentence_id),
            loop=self.conn.loop,
        )
        future.result(timeout=10)
        logger.info("TTS会话结束成功")
        
        # 等待一小段时间确保会话完全结束
        time.sleep(0.5)
```

#### 第2步：结束会话（aliyun_stream.py 第372-401行）
```python
async def finish_session(self, session_id):
    try:
        if self.ws:
            # 🔥 发送 StopSynthesis 请求到 TTS 服务器
            stop_request = {
                "header": {
                    "message_id": self.message_id,
                    "task_id": self.conn.sentence_id,
                    "namespace": "FlowingSpeechSynthesizer",
                    "name": "StopSynthesis",  # ← 停止合成会话
                    "appkey": self.appkey,
                }
            }
            await self.ws.send(json.dumps(stop_request))
            logger.info("会话结束请求已发送")
            
            # 等待监听任务完成
            if self._monitor_task:
                await self._monitor_task
                self._monitor_task = None
    except Exception as e:
        logger.error(f"关闭会话失败: {str(e)}")
        # 🔥 确保清理资源
        await self.close()
```

#### 第3步：清理资源（aliyun_stream.py 第403-421行）
```python
async def close(self):
    """资源清理"""
    # 取消监听任务
    if self._monitor_task:
        try:
            self._monitor_task.cancel()
            await self._monitor_task
        except asyncio.CancelledError:
            pass
        self._monitor_task = None
    
    # 🔥 关闭 WebSocket 连接
    if self.ws:
        try:
            await self.ws.close()
        except:
            pass
        self.ws = None
        self.last_active_time = None
```

---

## 📊 完整流程图

```
teaching_handler.py                     TTS Provider                    TTS 服务器
      │                                      │                              │
      │ 1. 生成 sentence_id                   │                              │
      │────────────────────────>              │                              │
      │                                      │                              │
      │ 2. put(FIRST)                        │                              │
      │────────────────────────>             │                              │
      │                                      │ 3. _ensure_connection()     │
      │                                      │    (建立 WebSocket)          │
      │                                      │─────────────────────────────>│
      │                                      │                              │
      │                                      │ 4. send(StartSynthesis)     │
      │                                      │─────────────────────────────>│
      │                                      │<─────────────────────────────│
      │                                      │    SessionStarted            │
      │                                      │                              │
      │ 5. put(MIDDLE, text)                │                              │
      │────────────────────────>             │                              │
      │                                      │ 6. send(text)               │
      │                                      │─────────────────────────────>│
      │                                      │<─────────────────────────────│
      │                                      │    音频流数据                 │
      │                                      │                              │
      │ 7. put(LAST)                        │                              │
      │────────────────────────>             │                              │
      │                                      │ 8. send(StopSynthesis)      │
      │                                      │─────────────────────────────>│
      │                                      │                              │
      │                                      │ 9. ws.close()               │
      │                                      │─────────────────────────────>│
      │                                      │                              │
      │ 10. 清空 sentence_id                 │                              │
      │────────────────────────>             │                              │
```

---

## 🎯 关键总结

### 建立新连接：
1. **应用层**：`put(SentenceType.FIRST)` → 发送 FIRST 请求到队列
2. **TTS层**：`start_session()` → 建立 WebSocket 连接
3. **网络层**：`websockets.connect()` → 实际的 TCP/WebSocket 连接
4. **服务层**：发送 `StartSynthesis` 请求到 TTS 服务器

### 结束连接：
1. **应用层**：`put(SentenceType.LAST)` → 发送 LAST 请求到队列
2. **TTS层**：`finish_session()` → 发送停止合成请求
3. **服务层**：发送 `StopSynthesis` 请求到 TTS 服务器
4. **网络层**：`ws.close()` → 关闭 WebSocket 连接
5. **清理**：清空 `sentence_id`，释放所有资源

### 每句话独立：
- 每句话都有独立的 `sentence_id`
- 每句话都建立独立的 WebSocket 连接
- 每句话结束后完全关闭连接，不复用
- 下一句话重新建立新的连接

---

## 📝 代码位置索引

| 功能 | 文件 | 行号 | 说明 |
|-----|------|------|------|
| 发送 FIRST | teaching_handler.py | 473-481 | 建立新连接入口 |
| 处理 FIRST | aliyun_stream.py | 217-247 | 检测并调用 start_session |
| start_session | aliyun_stream.py | 325-370 | 建立 WebSocket 并启动会话 |
| _ensure_connection | aliyun_stream.py | 179-207 | 实际建立 WebSocket 连接 |
| 发送 LAST | teaching_handler.py | 496-503 | 结束连接入口 |
| 处理 LAST | huoshan_double_stream.py | 374-387 | 检测并调用 finish_session |
| finish_session | aliyun_stream.py | 372-401 | 发送停止合成请求 |
| close | aliyun_stream.py | 403-421 | 关闭 WebSocket 连接 |

---

## ✅ 验证方法

运行时日志应该显示：
```
📤 [句1] 发送 FIRST (StartSession), sentence_id=abc12345...
开始会话～～abc12345
WebSocket 连接建立成功
会话启动请求已发送
📝 [句1] 发送 MIDDLE (文本): 你好
🏁 [句1] 发送 LAST (结束Session)
关闭会话～～abc12345
会话结束请求已发送
TTS会话结束成功

📤 [句2] 发送 FIRST (StartSession), sentence_id=def67890...
开始会话～～def67890
WebSocket 连接建立成功
会话启动请求已发送
...
```

每句话都是独立的完整生命周期！

