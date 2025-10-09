# 场景教学功能重构文档

## 概述

本次重构将 `connection.py` 中的场景教学相关功能独立出来，创建了专门的 `TeachingHandler` 类来处理所有教学相关的逻辑。

## 重构内容

### 1. 新增文件

#### `core/scenario/teaching_handler.py`
- **功能**: 场景教学处理器，负责处理所有教学相关的功能
- **主要方法**:
  - `handle_chat_mode()`: 处理聊天模式切换和教学模式逻辑
  - `_send_tts_message()`: 发送TTS消息
  - `_end_tts_session()`: 结束TTS会话
  - `_start_teaching_timeout_check()`: 启动教学超时检查
  - `cleanup()`: 清理教学处理器资源

### 2. 修改文件

#### `core/connection.py`
- **移除的功能**:
  - `_handle_chat_mode()`: 原有的复杂教学处理逻辑
  - `_send_tts_message()`: TTS消息发送逻辑
  - `_start_teaching_timeout_check()`: 超时检查逻辑
  - `ChatStatusManager` 的直接使用

- **新增的功能**:
  - `TeachingHandler` 实例的初始化
  - 简化的 `_handle_chat_mode()` 方法，委托给 `TeachingHandler`
  - 使用 `TeachingHandler` 的清理方法

### 3. 架构改进

#### 职责分离
- **ConnectionHandler**: 专注于连接管理、消息路由、LLM对话等核心功能
- **TeachingHandler**: 专注于场景教学、模式切换、超时管理等教学相关功能

#### 代码组织
- 教学相关逻辑集中在一个文件中，便于维护和扩展
- 减少了 `connection.py` 的复杂度，提高了可读性
- 更好的模块化设计，便于单元测试

## 使用方式

### 在 ConnectionHandler 中

```python
# 初始化时创建 TeachingHandler
self.teaching_handler = TeachingHandler(self)

# 处理聊天模式时委托给 TeachingHandler
def _handle_chat_mode(self, query):
    return self.teaching_handler.handle_chat_mode(query)

# 清理时调用 TeachingHandler 的清理方法
await self.teaching_handler.cleanup()
```

### 直接使用 TeachingHandler

```python
from core.scenario.teaching_handler import TeachingHandler

# 创建处理器
teaching_handler = TeachingHandler(connection)

# 设置儿童姓名
teaching_handler.set_child_name("小明")

# 处理聊天模式
result = teaching_handler.handle_chat_mode("切换到教学模式")

# 清理资源
await teaching_handler.cleanup()
```

## 测试

运行测试文件验证重构是否正确：

```bash
cd main/xiaozhi-server
python test_teaching_handler.py
```

## 优势

1. **模块化**: 教学功能独立成模块，便于维护和扩展
2. **可测试性**: 可以独立测试教学功能，不依赖完整的连接系统
3. **可复用性**: TeachingHandler 可以在其他场景中复用
4. **代码清晰**: 职责分离，代码结构更清晰
5. **易于扩展**: 新增教学功能时只需要修改 TeachingHandler

## 注意事项

1. **依赖关系**: TeachingHandler 依赖于 ConnectionHandler 的某些属性，需要确保这些属性在初始化时可用
2. **异步处理**: 教学功能涉及异步操作，需要正确处理事件循环
3. **资源清理**: 确保在连接关闭时正确清理教学相关的资源
4. **错误处理**: 教学功能中的错误不会影响核心连接功能

## 后续改进

1. **配置化**: 将教学相关的配置参数提取到配置文件中
2. **插件化**: 支持教学场景的插件化扩展
3. **监控**: 添加教学功能的性能监控和日志记录
4. **缓存**: 优化教学场景的缓存机制
