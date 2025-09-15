# 教学场景成功条件分支配置更新

## 更新概述

根据用户需求，移除了教学场景中步骤的替代消息处理逻辑，改为根据用户输入后的评估结果，使用成功条件分支配置进行跳转。**现在系统完全依赖三个分支配置，不再使用 `nextStepId` 字段。**

## 主要修改

### 1. 移除替代消息处理

- **文件**: `core/scenario/chat_status_manager.py`
- **修改**: 在 `_evaluate_response_with_config` 方法中移除了 `alternative_message` 字段
- **影响**: 不再使用步骤配置中的 `alternativeMessage` 字段

### 2. 实现成功条件分支跳转逻辑

- **文件**: `core/scenario/chat_status_manager.py`
- **修改**: 在 `_process_teaching_response` 方法中实现了基于评估分数的分支跳转逻辑
- **逻辑**:
  - 分数 >= 90: 使用 `perfectMatchNextStepId` 或 `exactMatchStepId` 跳转
  - 分数 60-89: 使用 `partialMatchNextStepId` 或 `partialMatchStepId` 跳转  
  - 分数 < 60: 使用 `noMatchNextStepId` 或 `noMatchStepId` 跳转
- **重要**: 如果分支配置不存在，系统会结束教学，不再使用 `nextStepId` 作为回退

### 3. 更新评估结果处理

- **文件**: `core/scenario/dialogue_service.py`
- **修改**: 在 `_evaluate_response` 方法中移除了替代消息相关逻辑
- **影响**: 评估结果不再包含 `alternative_message` 字段

### 4. 更新超时处理逻辑

- **文件**: `core/scenario/chat_status_manager.py`
- **修改**: 在 `check_teaching_timeout` 方法中更新了超时后的跳转逻辑
- **逻辑**: 超时后使用 `noMatchNextStepId` 或 `noMatchStepId` 进行跳转
- **重要**: 如果超时后没有配置 `noMatchStepId`，系统会结束教学

## 分支配置字段

### 步骤配置中的新字段

系统支持两种字段命名方式：

**新字段名称（推荐）：**
```json
{
  "perfectMatchNextStepId": "step_advanced",    // 完全匹配分支跳转
  "partialMatchNextStepId": "step_normal",      // 部分匹配分支跳转
  "noMatchNextStepId": "step_basic"             // 完全不匹配分支跳转
}
```

**兼容旧字段名称：**
```json
{
  "exactMatchStepId": "step_advanced",          // 完全匹配分支跳转
  "partialMatchStepId": "step_normal",          // 部分匹配分支跳转
  "noMatchStepId": "step_basic"                 // 完全不匹配分支跳转
}
```

系统会优先使用新字段名称，如果新字段不存在则使用旧字段名称，确保向后兼容性。

### 分数阈值

- **完全匹配**: 分数 >= 90
- **部分匹配**: 分数 60-89
- **完全不匹配**: 分数 < 60

## 返回结果更新

### 新的action类型

- `perfect_match_next`: 完全匹配分支跳转
- `partial_match_next`: 部分匹配分支跳转
- `no_match_next`: 完全不匹配分支跳转

### 返回结果字段

```json
{
  "success": true,
  "action": "perfect_match_next",
  "branch_type": "perfect_match",
  "current_step": {...},
  "evaluation": {...},
  "message": "根据perfect_match分支进入下一步：太棒了！你回答得很好！"
}
```

## 重要变更

### 移除 nextStepId 依赖

- **重要**: 系统不再使用 `nextStepId` 字段作为回退机制
- **新行为**: 如果步骤配置中没有设置分支跳转字段，系统会结束教学
- **原因**: 确保所有步骤都必须明确配置三个分支的跳转逻辑

### 分支配置要求

- **必须配置**: 每个步骤都必须配置三个分支字段
- **推荐配置**: 使用新字段名称（`perfectMatchNextStepId` 等）
- **兼容支持**: 仍然支持旧字段名称（`exactMatchStepId` 等）

### 教学结束条件

系统会在以下情况下结束教学：
1. 没有配置对应的分支跳转字段
2. 分支跳转的步骤ID不存在
3. 超时且没有配置 `noMatchStepId`
4. 完成所有配置的步骤

## 使用示例

### 步骤配置示例

```json
{
  "id": "step_1",
  "stepName": "问候步骤",
  "aiMessage": "你好，{childName}！",
  "expectedKeywords": "[\"你好\", \"准备好了\"]",
  "expectedPhrases": "[\"你好\", \"准备好了\", \"开始学习\"]",
  "successCondition": "partial",
  "praiseMessage": "太棒了！你回答得很好！",
  "encouragementMessage": "加油！你可以做得更好！",
  "perfectMatchNextStepId": "step_advanced",
  "partialMatchNextStepId": "step_normal",
  "noMatchNextStepId": "step_basic",
  "timeoutSeconds": 20
}
```

### 分支跳转逻辑

1. **用户输入**: "你好，我准备好了，开始学习"
2. **评估结果**: 分数 100 (完全匹配)
3. **分支跳转**: 使用 `perfectMatchNextStepId` 跳转到 `step_advanced`
4. **返回结果**: `action: "perfect_match_next"`

## 测试验证

已通过测试验证以下功能：
- ✅ 分支跳转逻辑正常工作
- ✅ 不同分数对应正确的分支类型
- ✅ 跳转步骤ID正确获取
- ✅ 评估结果正确生成
- ✅ 向后兼容性保持

## 注意事项

1. **步骤ID必须唯一**: 每个步骤的ID在整个场景中必须唯一
2. **跳转步骤必须存在**: 配置的跳转步骤ID必须在场景中存在
3. **避免循环跳转**: 避免配置导致无限循环的跳转
4. **分数阈值可调整**: 可以根据需要调整分数阈值

## 相关文档

- [三分支步骤配置示例](../THREE_BRANCH_CONFIG_EXAMPLE.md)
- [场景流程图](../core/scenario/SCENARIO_FLOW_DIAGRAM.md)
