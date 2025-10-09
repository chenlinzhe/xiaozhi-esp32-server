# 小智服务器聊天功能自动化测试

基于 `test_page.html` 的功能，创建了完整的Python自动化测试工具，用于测试小智服务器的所有聊天相关功能。

## 功能特性

### 🧪 测试覆盖范围

1. **OTA连接测试** - 测试设备OTA连接和认证
2. **WebSocket连接测试** - 测试WebSocket连接和握手
3. **自由聊天测试** - 测试基本的自由聊天功能
4. **教学模式测试** - 测试教学模式切换和教学流程
5. **MCP功能测试** - 测试MCP协议和设备控制功能
6. **错误处理测试** - 测试异常情况的处理

### 📊 测试报告

- 详细的测试结果报告
- 测试耗时统计
- 错误信息记录
- 对话历史保存
- JSON格式的详细日志

## 安装依赖

```bash
pip install websockets requests
```

## 使用方法

### 1. 基本使用

```bash
# 运行所有测试
python test_chat_automation.py

# 或者使用运行脚本
python run_chat_test.py
```

### 2. 运行特定测试

```bash
# 只测试OTA连接
python run_chat_test.py --test ota

# 只测试WebSocket连接
python run_chat_test.py --test websocket

# 只测试教学模式
python run_chat_test.py --test teaching

# 只测试自由聊天
python run_chat_test.py --test free_chat

# 只测试MCP功能
python run_chat_test.py --test mcp

# 只测试错误处理
python run_chat_test.py --test error
```

### 3. 自定义配置

创建 `test_config.json` 文件：

```json
{
  "ota_url": "http://127.0.0.1:8002/xiaozhi/ota/",
  "ws_url": "ws://127.0.0.1:8000/xiaozhi/v1/",
  "device_name": "Python测试设备",
  "client_id": "python_test_client",
  "token": "your-token1"
}
```

然后运行：

```bash
python run_chat_test.py --config test_config.json
```

## 测试流程

### 1. OTA连接测试
- 发送设备信息到OTA服务器
- 验证设备认证和版本检查
- 检查是否需要激活码

### 2. WebSocket连接测试
- 建立WebSocket连接
- 发送hello握手消息
- 验证会话ID分配

### 3. 自由聊天测试
- 发送多个测试消息
- 验证大模型回复
- 检查TTS和STT功能

### 4. 教学模式测试
- 切换到教学模式
- 回答教学问题
- 验证智能评估
- 切换回自由模式

### 5. MCP功能测试
- 等待MCP消息
- 模拟客户端回复
- 验证工具列表和调用

### 6. 错误处理测试
- 发送空消息
- 发送超长消息
- 发送特殊字符

## 输出文件

测试完成后会生成以下文件：

- `chat_test.log` - 详细日志文件
- `chat_test_report.txt` - 测试报告（文本格式）
- `chat_test_details.json` - 详细测试数据（JSON格式）

## 测试报告示例

```
============================================================
聊天功能自动化测试报告
============================================================

测试概览:
- 总测试数: 6
- 通过: 5 ✅
- 失败: 1 ❌
- 跳过: 0 ⚠️
- 总耗时: 45.23秒

详细结果:

✅ OTA连接测试 (2.15秒)

✅ WebSocket连接测试 (1.87秒)

✅ 自由聊天测试 (12.34秒)

✅ 教学模式测试 (15.67秒)

❌ MCP功能测试 (8.20秒)
   错误: 未收到MCP消息，可能服务器未启用MCP功能

✅ 错误处理测试 (5.00秒)

对话历史 (12 条):
1. 用户: 你好
2. 服务器(llm): 你好！我是小智，很高兴为您服务。
3. 用户: 教学模式
4. 服务器(tts): 已切换到教学模式，开始学习场景：喝水教学
...
```

## 故障排除

### 常见问题

1. **OTA连接失败**
   - 检查OTA服务器是否启动
   - 确认URL配置正确
   - 检查设备认证配置

2. **WebSocket连接失败**
   - 检查WebSocket服务器是否启动
   - 确认端口配置正确
   - 检查防火墙设置

3. **教学模式测试失败**
   - 确认教学场景已配置
   - 检查数据库连接
   - 验证API认证

4. **MCP功能测试跳过**
   - 这是正常的，如果服务器未启用MCP功能
   - 不影响其他功能测试

### 调试建议

1. 查看详细日志文件 `chat_test.log`
2. 检查服务器日志
3. 确认所有服务都已启动
4. 验证网络连接

## 系统要求

- Python 3.7+
- 小智服务器已启动
- 网络连接正常
- 相关依赖已安装

## 开发说明

### 添加新测试

1. 在 `ChatAutomationTester` 类中添加新的测试方法
2. 在 `run_all_tests` 方法中注册新测试
3. 在 `run_specific_test` 中添加测试映射

### 自定义测试数据

修改测试消息和期望响应：

```python
# 在 test_free_chat 方法中
test_messages = [
    "你好",
    "今天天气怎么样？",
    "讲个笑话",
    "谢谢"
]
```

### 扩展测试配置

在配置文件中添加新的配置项：

```json
{
  "ota_url": "http://127.0.0.1:8002/xiaozhi/ota/",
  "ws_url": "ws://127.0.0.1:8000/xiaozhi/v1/",
  "device_name": "Python测试设备",
  "client_id": "python_test_client",
  "token": "your-token1",
  "timeout": 30,
  "retry_count": 3
}
```

## 许可证

本项目遵循MIT许可证。
