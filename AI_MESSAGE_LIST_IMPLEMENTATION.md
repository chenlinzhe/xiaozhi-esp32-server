# AI消息列表功能实现说明

## 概述

本次更新为步骤配置添加了AI消息列表支持，每个步骤可以有多个AI消息，每个消息可以独立配置语速、等待时间、参数等。系统完全向后兼容，现有功能不受影响。

## 功能特性

### 1. 消息模式切换
- **单个消息模式**：保持原有的单个AI消息配置方式
- **消息列表模式**：支持每个步骤配置多个AI消息

### 2. 消息配置项
每个AI消息包含以下配置：
- **消息内容**：AI要说的具体内容
- **语速配置**：0.5-2.0倍速，支持慢速、正常、快速等
- **等待时间**：每条消息播放后的等待时间（秒）
- **消息参数**：JSON格式，支持情绪、语调、音量等参数
- **消息类型**：普通、指令、鼓励、反馈等
- **启用状态**：可以启用/禁用特定消息

### 3. 消息管理功能
- **增删改查**：完整的消息CRUD操作
- **顺序调整**：支持消息的上下移动和重新排序
- **批量保存**：一次性保存所有消息配置

## 技术实现

### 1. 数据库设计

#### 新增表：ai_step_message
```sql
CREATE TABLE `ai_step_message` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `message_id` varchar(64) NOT NULL COMMENT '消息唯一标识',
  `step_id` varchar(64) NOT NULL COMMENT '关联的步骤ID',
  `scenario_id` varchar(64) NOT NULL COMMENT '关联的场景ID',
  `message_content` text NOT NULL COMMENT 'AI消息内容',
  `message_order` int(11) NOT NULL DEFAULT 1 COMMENT '消息顺序',
  `speech_rate` decimal(3,1) DEFAULT 1.0 COMMENT '语速配置',
  `wait_time_seconds` int(11) DEFAULT 3 COMMENT '等待时间（秒）',
  `parameters` text COMMENT '消息参数，JSON格式',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `message_type` varchar(32) DEFAULT 'normal' COMMENT '消息类型',
  -- 其他标准字段...
);
```

#### 修改现有表
为 `ai_scenario_step` 和 `ai_step_template` 表添加字段：
- `use_message_list`：是否使用消息列表
- `message_list_config`：消息列表配置

### 2. 后端架构

#### 新增组件
- **StepMessageEntity**：AI消息实体类
- **StepMessageMapper**：数据访问层
- **StepMessageService**：业务逻辑层
- **StepMessageController**：REST API接口

#### 现有组件增强
- **ScenarioStepEntity**：添加消息列表支持
- **ScenarioStepService**：集成消息列表功能
- **ScenarioStepController**：支持消息列表的步骤保存

### 3. 前端架构

#### 新增组件
- **StepMessageList.vue**：AI消息列表管理组件

#### 现有页面增强
- **ScenarioStepConfig.vue**：集成消息列表功能，支持模式切换

## 使用方法

### 1. 数据库升级
执行数据库变更脚本：
```sql
-- 执行文件：main/manager-api/src/main/resources/db/changelog/20250101_ai_message_list.sql
```

### 2. 后端部署
- 重新编译并部署manager-api服务
- 确保所有新增的Java类都已正确部署

### 3. 前端部署
- 重新编译并部署manager-web服务
- 确保StepMessageList组件已正确部署

### 4. 功能使用

#### 步骤配置页面
1. 在步骤配置中选择"消息列表"模式
2. 点击"添加消息"按钮添加新的AI消息
3. 为每条消息配置内容、语速、等待时间等参数
4. 使用上下箭头调整消息顺序
5. 点击"保存消息列表"保存配置

#### API接口
- `GET /step-message/list/{stepId}` - 获取步骤消息列表
- `POST /step-message/batch-save/{stepId}` - 批量保存步骤消息
- `DELETE /step-message/{id}` - 删除消息
- `POST /step-message/reorder/{stepId}` - 重新排序消息

## 兼容性说明

### 1. 向后兼容
- 现有步骤配置完全不受影响
- 原有的单个AI消息功能保持不变
- 数据库自动迁移现有数据

### 2. 数据迁移
- 执行脚本后，现有ai_message数据自动迁移到消息列表表
- 迁移后的数据保持原有配置（语速、等待时间等）

### 3. 渐进式升级
- 可以逐步将现有步骤从单个消息模式切换到消息列表模式
- 两种模式可以并存，互不影响

## 配置示例

### 1. 单个消息模式（原有方式）
```json
{
  "useMessageList": 0,
  "aiMessage": "你好，小朋友！",
  "speechRate": 1.0,
  "waitTimeSeconds": 3
}
```

### 2. 消息列表模式（新功能）
```json
{
  "useMessageList": 1,
  "stepMessages": [
    {
      "messageContent": "你好，小朋友！",
      "speechRate": 1.0,
      "waitTimeSeconds": 2,
      "parameters": "{\"emotion\": \"friendly\", \"tone\": \"gentle\"}",
      "messageType": "normal"
    },
    {
      "messageContent": "今天我们来学习一些有趣的东西",
      "speechRate": 0.8,
      "waitTimeSeconds": 3,
      "parameters": "{\"emotion\": \"excited\", \"tone\": \"enthusiastic\"}",
      "messageType": "instruction"
    },
    {
      "messageContent": "准备好了吗？",
      "speechRate": 1.2,
      "waitTimeSeconds": 2,
      "parameters": "{\"emotion\": \"encouraging\", \"tone\": \"questioning\"}",
      "messageType": "feedback"
    }
  ]
}
```

## 注意事项

### 1. 性能考虑
- 消息列表数量建议控制在10条以内
- 大量消息可能影响步骤加载性能

### 2. 数据一致性
- 消息列表与步骤配置同步保存
- 删除步骤时自动删除相关消息

### 3. 错误处理
- 消息参数必须是有效的JSON格式
- 消息内容不能为空
- 语速和等待时间有合理范围限制

## 扩展功能

### 1. 消息模板
- 支持预定义的消息模板
- 快速应用常用配置

### 2. 消息预览
- 支持消息内容的预览播放
- 测试语速和等待时间效果

### 3. 批量导入
- 支持从Excel或CSV批量导入消息
- 提高配置效率

## 总结

AI消息列表功能为步骤配置提供了更灵活和强大的配置能力，支持复杂的教学场景需求。通过向后兼容的设计，确保现有系统平稳升级，新功能可以逐步应用。该功能为未来的AI教学场景扩展奠定了良好的基础。
