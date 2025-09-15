# 用户信息管理功能使用说明

## 功能概述

用户信息管理功能可以自动检测设备绑定的用户信息，如果没有用户姓名，会在第一句话时询问用户的名字并保存。同时支持用户知识库管理，可以记录和存储用户的相关信息。

## 主要功能

### 1. 用户信息检测
- 自动检测设备是否已绑定用户信息
- 检查用户是否已设置姓名
- 记录用户交互次数和最后交互时间

### 2. 智能姓名收集
- 自动识别用户输入中的姓名信息
- 支持多种姓名表达方式（"我叫张三"、"我的名字是李四"等）
- 验证姓名有效性，过滤无效输入

### 3. 用户知识库
- 存储用户相关信息
- 支持JSON格式的结构化数据
- 自动更新和扩展知识库内容

### 4. 个性化交互
- 根据用户姓名进行个性化称呼
- 基于用户历史信息提供更好的服务
- 记录用户偏好和习惯

## 数据库表结构

### user_info 表
```sql
CREATE TABLE user_info (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL UNIQUE,
    user_name VARCHAR(100),
    user_nickname VARCHAR(100),
    user_age INT,
    user_gender TINYINT,
    user_avatar VARCHAR(500),
    user_preferences TEXT,
    knowledge_base TEXT,
    first_interaction_time DATETIME,
    last_interaction_time DATETIME,
    interaction_count INT DEFAULT 0,
    is_active TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### user_interaction_log 表
```sql
CREATE TABLE user_interaction_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    user_name VARCHAR(100),
    interaction_type VARCHAR(50),
    user_input TEXT,
    ai_response TEXT,
    interaction_duration INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 配置说明

在 `config.yaml` 中添加以下配置：

```yaml
# 用户信息管理配置
user_info_management:
  # 是否启用用户信息管理
  enabled: true
  # 是否在首次连接时自动检查用户信息
  auto_check_on_first_connection: true
  # 是否自动收集用户姓名
  auto_collect_name: true
  # 姓名收集提示语
  name_collection_prompts:
    - "你好！我是小智，很高兴认识你！请问你叫什么名字呢？"
    - "欢迎使用小智！为了能更好地为你服务，请告诉我你的名字吧！"
    - "你好！我是你的AI助手小智，请问怎么称呼你呢？"
    - "很高兴见到你！请告诉我你的名字，这样我就能更好地记住你了！"
  # 知识库管理
  knowledge_base:
    # 是否启用知识库功能
    enabled: true
    # 知识库最大大小（字符数）
    max_size: 10000
    # 是否自动保存用户相关信息到知识库
    auto_save_user_info: true

# 在function_call配置中添加用户信息管理功能
Intent:
  function_call:
    functions:
      - check_user_info
      - collect_user_name
      - update_knowledge_base
      - get_user_info
      - smart_name_collector
      - user_info_intent
```

## 可用的Function Call

### 1. check_user_info
检测用户信息状态，如果没有姓名则询问用户姓名。

**参数**: 无

**返回**: 根据用户状态返回相应的问候语或姓名询问

### 2. collect_user_name
收集并保存用户的姓名信息。

**参数**:
- `user_name` (string): 用户提供的姓名

**返回**: 确认保存成功的消息

### 3. update_knowledge_base
更新用户的知识库信息。

**参数**:
- `knowledge_info` (string): 要添加到知识库的信息

**返回**: 确认更新成功的消息

### 4. get_user_info
获取当前用户的基本信息和知识库。

**参数**: 无

**返回**: 用户信息摘要

### 5. smart_name_collector
智能识别用户输入中的姓名信息。

**参数**:
- `user_input` (string): 用户的输入内容

**返回**: 如果检测到姓名则自动保存并确认

### 6. user_info_intent
检测用户信息状态，如果是新用户或没有姓名则引导用户提供姓名。

**参数**:
- `user_input` (string): 用户的输入内容

**返回**: 根据用户状态进行相应处理

## 使用流程

### 1. 新用户首次连接
1. 用户连接设备
2. 系统自动检测用户信息
3. 发现用户没有姓名，自动询问姓名
4. 用户提供姓名后，系统保存并确认
5. 后续交互中使用用户姓名进行个性化称呼

### 2. 老用户连接
1. 用户连接设备
2. 系统检测到已有用户信息
3. 使用用户姓名进行个性化问候
4. 正常进行对话交互

### 3. 知识库管理
1. 用户可以通过对话提供个人信息
2. 系统自动识别并保存到知识库
3. 后续交互中可以参考知识库信息
4. 支持手动更新知识库内容

## API接口

### 后端API接口

#### 获取用户信息
```
GET /user/info?deviceId={deviceId}
```

#### 检查用户是否有姓名
```
GET /user/has-name?deviceId={deviceId}
```

#### 更新用户姓名
```
POST /user/update-name
{
    "deviceId": "设备ID",
    "userName": "用户姓名"
}
```

#### 更新用户知识库
```
POST /user/update-knowledge
{
    "deviceId": "设备ID",
    "knowledgeBase": "知识库内容"
}
```

#### 获取用户知识库
```
GET /user/knowledge?deviceId={deviceId}
```

#### 记录用户交互
```
POST /user/interaction
{
    "deviceId": "设备ID",
    "interactionType": "交互类型",
    "userInput": "用户输入",
    "aiResponse": "AI回复"
}
```

## 部署步骤

### 1. 数据库部署
```bash
# 执行数据库脚本
mysql -u root -p your_database < main/manager-api/src/main/resources/db/changelog/202501200000_create_user_info_table.sql
```

### 2. 后端部署
```bash
# 编译后端项目
cd main/manager-api
mvn clean package -DskipTests

# 启动后端服务
java -jar target/manager-api.jar
```

### 3. 前端配置
确保前端配置中包含了用户信息管理相关的API调用。

### 4. 小智服务端配置
在 `config.yaml` 中启用用户信息管理功能，并添加相应的function call配置。

## 注意事项

1. **设备ID唯一性**: 每个设备ID只能绑定一个用户信息
2. **姓名验证**: 系统会自动验证姓名的有效性，过滤无效输入
3. **知识库大小**: 建议控制知识库大小，避免影响性能
4. **隐私保护**: 用户信息需要妥善保护，建议加密存储敏感信息
5. **错误处理**: 系统包含完善的错误处理机制，确保服务稳定性

## 扩展功能

### 1. 用户偏好设置
可以扩展用户偏好设置功能，记录用户的个性化需求。

### 2. 多用户支持
可以扩展支持一个设备绑定多个用户的功能。

### 3. 用户画像
基于用户交互数据生成用户画像，提供更精准的服务。

### 4. 数据统计
提供用户交互数据统计和分析功能。

## 故障排除

### 1. 用户信息无法保存
- 检查数据库连接是否正常
- 确认API服务是否正常运行
- 检查设备ID是否正确

### 2. 姓名识别不准确
- 检查姓名验证规则是否合适
- 调整姓名提取的正则表达式
- 增加更多的姓名模式匹配

### 3. 知识库更新失败
- 检查知识库大小是否超限
- 确认JSON格式是否正确
- 检查数据库字段长度限制

## 更新日志

### v1.0.0 (2025-01-20)
- 初始版本发布
- 支持基本的用户信息管理
- 实现智能姓名收集功能
- 添加用户知识库管理
- 集成到function call系统

