# 三分支步骤配置示例

## 功能说明

现在每个步骤支持三个分支，根据用户回答的匹配程度跳转到不同的步骤：

1. **完全匹配分支** (分数 >= 90)：用户回答完全符合预期
2. **部分匹配分支** (60 <= 分数 < 90)：用户回答部分符合预期
3. **完全不匹配分支** (分数 < 60)：用户回答不符合预期

## 步骤配置字段

### 基础字段
```json
{
  "id": "step_1",
  "stepName": "问候步骤",
  "stepOrder": 1,
  "aiMessage": "你好，{childName}！",
  "aiMessageList": "[\"欢迎来到学习课堂！\", \"今天我们要学习什么呢？\"]",
  "expectedKeywords": "[\"你好\", \"准备好了\"]",
  "alternativeMessage": "让我们重新开始吧！",
  "timeoutSeconds": 20
}
```

### 分支跳转字段
```json
{
  // 完全匹配分支 - 跳转到指定步骤
  "perfectMatchNextStepId": "step_advanced",
  
  // 部分匹配分支 - 跳转到指定步骤
  "partialMatchNextStepId": "step_review",
  
  // 完全不匹配分支 - 跳转到指定步骤
  "noMatchNextStepId": "step_basic"
}
```

## 完整配置示例

### 步骤1：问候步骤
```json
{
  "id": "step_1",
  "stepName": "问候步骤",
  "stepOrder": 1,
  "aiMessage": "你好，{childName}！欢迎来到学习课堂！",
  "aiMessageList": "[\"你好，{childName}！\", \"欢迎来到学习课堂！\", \"今天我们要学习什么呢？\"]",
  "expectedKeywords": "[\"你好\", \"准备好了\", \"开始学习\"]",
  "alternativeMessage": "没关系，让我们重新开始吧！",
  "timeoutSeconds": 20,
  "perfectMatchNextStepId": "step_2_advanced",
  "partialMatchNextStepId": "step_2_normal",
  "noMatchNextStepId": "step_1_retry"
}
```

### 步骤2：高级学习步骤
```json
{
  "id": "step_2_advanced",
  "stepName": "高级学习步骤",
  "stepOrder": 2,
  "aiMessage": "太棒了！你回答得很好！让我们学习更高级的内容。",
  "aiMessageList": "[\"太棒了！你回答得很好！\", \"让我们学习更高级的内容。\", \"准备好了吗？\"]",
  "expectedKeywords": "[\"准备好了\", \"开始\", \"学习\"]",
  "alternativeMessage": "加油！你可以做得更好！",
  "timeoutSeconds": 25,
  "perfectMatchNextStepId": "step_3_expert",
  "partialMatchNextStepId": "step_3_advanced",
  "noMatchNextStepId": "step_2_normal"
}
```

### 步骤3：普通学习步骤
```json
{
  "id": "step_2_normal",
  "stepName": "普通学习步骤",
  "stepOrder": 2,
  "aiMessage": "不错！让我们继续学习基础内容。",
  "aiMessageList": "[\"不错！\", \"让我们继续学习基础内容。\", \"准备好了吗？\"]",
  "expectedKeywords": "[\"准备好了\", \"开始\"]",
  "alternativeMessage": "没关系，我们再试一次！",
  "timeoutSeconds": 20,
  "perfectMatchNextStepId": "step_3_advanced",
  "partialMatchNextStepId": "step_3_normal",
  "noMatchNextStepId": "step_1_retry"
}
```

### 步骤4：重试步骤
```json
{
  "id": "step_1_retry",
  "stepName": "重试步骤",
  "stepOrder": 1,
  "aiMessage": "没关系，让我们重新开始！",
  "aiMessageList": "[\"没关系，让我们重新开始！\", \"这次我们慢慢来。\", \"准备好了吗？\"]",
  "expectedKeywords": "[\"准备好了\", \"开始\"]",
  "alternativeMessage": "加油！我相信你可以的！",
  "timeoutSeconds": 30,
  "perfectMatchNextStepId": "step_2_normal",
  "partialMatchNextStepId": "step_2_normal",
  "noMatchNextStepId": "step_1_retry"
}
```

## 分支逻辑说明

### 1. 完全匹配分支 (分数 >= 90)
- 用户回答完全符合预期
- 跳转到 `perfectMatchNextStepId` 指定的步骤
- 如果没有配置，则按顺序进入下一步

### 2. 部分匹配分支 (60 <= 分数 < 90)
- 用户回答部分符合预期
- 跳转到 `partialMatchNextStepId` 指定的步骤
- 如果没有配置，则按顺序进入下一步

### 3. 完全不匹配分支 (分数 < 60)
- 用户回答不符合预期
- 跳转到 `noMatchNextStepId` 指定的步骤
- 如果没有配置，则重试当前步骤
- 重试次数达到3次后，强制进入下一步

## 使用场景

### 场景1：分层教学
- 完全匹配 → 高级内容
- 部分匹配 → 普通内容
- 完全不匹配 → 基础内容

### 场景2：个性化学习路径
- 完全匹配 → 快速通道
- 部分匹配 → 标准路径
- 完全不匹配 → 强化练习

### 场景3：错误处理
- 完全匹配 → 继续学习
- 部分匹配 → 补充说明
- 完全不匹配 → 重新讲解

## 注意事项

1. **步骤ID必须唯一**：每个步骤的ID在整个场景中必须唯一
2. **跳转步骤必须存在**：配置的跳转步骤ID必须在场景中存在
3. **避免循环跳转**：避免配置导致无限循环的跳转
4. **分数阈值可调整**：可以根据需要调整分数阈值
5. **向后兼容**：不配置分支字段时，系统按原有逻辑运行

## 配置建议

1. **为每个步骤配置合适的分支**：根据教学需求配置不同的跳转路径
2. **设置合理的分数阈值**：确保分支判断准确
3. **提供丰富的AI消息**：为不同分支提供不同的反馈
4. **测试分支逻辑**：确保所有分支都能正确跳转
