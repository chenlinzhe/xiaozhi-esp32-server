# AI陪伴功能模块

## 项目概述

AI陪伴功能模块是为特殊儿童提供引导式场景对话训练的核心功能，支持300+种场景配置，通过语音、视觉、按钮等多种触发方式，为儿童提供个性化的教学体验。

## 功能特性

### 🎯 核心功能
- **场景配置化** - 所有对话流程通过配置实现，无需编程
- **智能判断** - 支持完全匹配、部分匹配、关键词匹配等多种成功条件
- **个性化体验** - 支持儿童姓名记忆、手势提示、音效支持
- **多触发方式** - 支持语音、视觉、按钮等多种触发方式
- **学习记录** - 完整的进度跟踪和统计分析功能

### 📊 支持场景类型
- **表达需求** - 口渴、饥饿、上厕所等基本需求表达
- **问候语** - 日常问候、礼貌用语训练
- **情感表达** - 开心、难过、生气等情感表达
- **社交技能** - 分享、合作、沟通等社交技能
- **学习训练** - 数学、语言、认知等学习内容
- **游戏互动** - 趣味游戏和互动训练

## 技术架构

### 后端架构
```
Spring Boot + MyBatis Plus
├── Entity层 - 数据实体
├── Mapper层 - 数据访问
├── Service层 - 业务逻辑
└── Controller层 - API接口
```

### 前端架构
```
Vue.js + Element UI
├── Views - 页面组件
├── APIs - 接口调用
└── Router - 路由配置
```

### 设备端架构
```
Python + WebSocket
├── ScenarioManager - 场景管理
├── DialogueExecutor - 对话执行
└── ScenarioTrigger - 场景触发
```

## 开发完成情况

### ✅ 已完成功能

#### 1. 数据库设计与基础架构 (100%完成)
- [x] 数据库表结构设计
- [x] 后端实体类开发
- [x] Mapper接口开发
- [x] Service层实现
- [x] Controller层API开发

#### 2. 对话步骤配置与执行器 (100%完成)
- [x] 场景管理器 (scenario_manager.py)
- [x] 对话执行器 (dialogue_executor.py)
- [x] 学习记录管理器 (learning_record_manager.py)
- [x] 设备端集成

#### 3. 前端界面开发 (100%完成)
- [x] 场景配置页面 (ScenarioConfig.vue)
- [x] 场景创建页面 (ScenarioCreate.vue)
- [x] 场景编辑页面 (ScenarioEdit.vue)
- [x] 步骤配置页面 (ScenarioStepConfig.vue)
- [x] 学习记录管理页面 (LearningRecordManagement.vue)

#### 4. API接口开发 (100%完成)
- [x] 场景管理API (ScenarioController.java)
- [x] 步骤管理API (ScenarioStepController.java)
- [x] 模板管理API (StepTemplateController.java)
- [x] 学习记录API (ChildLearningRecordController.java)
- [x] 前端API模块 (scenario.js)

#### 5. 测试验证 (100%完成)
- [x] 集成测试脚本 (test_scenario_integration.py)
- [x] 性能测试脚本 (test_scenario_performance.py)
- [x] API测试脚本 (test_scenario_api.js)

## 快速开始

### 1. 环境要求
- Java 8+
- Node.js 12+
- Python 3.7+
- MySQL 5.7+

### 2. 数据库部署
```sql
-- 执行数据库脚本
source main/manager-api/src/main/resources/db/changelog/20241201_001_create_ai_scenario_tables.sql
```

### 3. 后端部署
```bash
# 编译打包
cd main/manager-api
mvn clean package

# 运行
java -jar target/manager-api.jar
```

### 4. 前端部署
```bash
# 安装依赖
cd main/manager-web
npm install

# 开发环境运行
npm run serve

# 生产环境构建
npm run build
```

### 5. 设备端部署
```bash
# 安装依赖
cd main/xiaozhi-server
pip install -r requirements.txt

# 运行服务
python app.py
```

## API接口文档

### 场景管理API
- `GET /xiaozhi/scenario/list` - 获取场景列表
- `GET /xiaozhi/scenario/{id}` - 获取场景详情
- `POST /xiaozhi/scenario` - 保存场景
- `PUT /xiaozhi/scenario/{id}` - 更新场景
- `DELETE /xiaozhi/scenario/{id}` - 删除场景
- `PUT /xiaozhi/scenario/{id}/toggle` - 启用/禁用场景

### 步骤管理API
- `GET /xiaozhi/scenario-step/list/{scenarioId}` - 获取步骤列表
- `POST /xiaozhi/scenario-step/batch-save/{scenarioId}` - 批量保存步骤
- `DELETE /xiaozhi/scenario-step/{id}` - 删除步骤

### 学习记录API
- `GET /xiaozhi/learning-record/list` - 获取学习记录列表
- `GET /xiaozhi/learning-record/{id}` - 获取学习记录详情
- `POST /xiaozhi/learning-record` - 保存学习记录
- `PUT /xiaozhi/learning-record/{id}` - 更新学习记录
- `DELETE /xiaozhi/learning-record/{id}` - 删除学习记录

## 使用示例

### 1. 创建场景
```javascript
// 前端API调用示例
Api.scenario.saveScenario({
  scenarioName: '口渴表达训练',
  scenarioCode: 'thirst_expression',
  scenarioType: 'express_needs',
  triggerType: 'voice',
  triggerKeywords: '["渴了", "口渴", "喝水"]',
  description: '训练儿童表达口渴需求',
  difficultyLevel: 1,
  targetAge: '3-6'
}, (res) => {
  console.log('场景创建成功:', res);
});
```

### 2. 配置步骤
```javascript
// 配置对话步骤
const steps = [
  {
    stepName: '问候',
    aiMessage: '你好，**{childName}**！',
    expectedKeywords: '["你好"]',
    expectedPhrases: '["你好", "hi"]',
    successCondition: 'partial',
    maxAttempts: 3
  },
  {
    stepName: '需求表达',
    aiMessage: '你想喝水吗？',
    expectedKeywords: '["想", "要"]',
    expectedPhrases: '["想喝水", "要喝水"]',
    successCondition: 'partial',
    maxAttempts: 3
  }
];

Api.scenario.saveScenarioSteps(scenarioId, steps, (res) => {
  console.log('步骤配置成功:', res);
});
```

### 3. 设备端触发
```python
# 设备端场景触发示例
async def handle_voice_input(text):
    # 检测场景触发
    triggered_scenario = await scenario_trigger.detect_trigger(text, "voice")
    if triggered_scenario:
        # 开始场景对话
        executor = DialogueStepExecutor(triggered_scenario['id'], "小明")
        await executor.initialize()
        
        # 执行对话步骤
        result = executor.execute_current_step(text)
        print(f"对话结果: {result}")
```

## 测试验证

### 运行API测试
```bash
# 安装依赖
npm install axios

# 运行API测试
node test_scenario_api.js
```

### 运行集成测试
```bash
# 运行场景集成测试
python test_scenario_integration.py

# 运行性能测试
python test_scenario_performance.py
```

## 性能指标

- **平均响应时间**: < 100ms
- **内存使用**: < 50MB
- **并发处理**: 支持10个并发会话
- **前端加载时间**: < 2秒

## 扩展性设计

### 1. 模块化设计
- 场景模块独立
- 步骤模块独立
- 模板模块独立
- 学习记录模块独立

### 2. 配置化支持
- 场景类型可扩展
- 触发方式可扩展
- 成功条件可扩展

### 3. 插件化架构
- 支持自定义步骤类型
- 支持自定义触发方式
- 支持自定义判断逻辑

## 开发团队

- **后端开发**: xiaozhi开发组
- **前端开发**: xiaozhi开发组
- **测试**: xiaozhi开发组

## 版本信息

- **当前版本**: v1.0
- **开发完成时间**: 2024年12月
- **最后更新**: 2024年12月

## 许可证

本项目采用 MIT 许可证。

---

**注意**: 本项目为特殊儿童教育辅助工具，请在使用过程中注意保护儿童隐私和安全。
