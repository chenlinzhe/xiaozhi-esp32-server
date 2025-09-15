# 三个分支配置最佳实践

## 概述

现在教学场景完全依赖三个分支配置进行跳转，不再使用 `nextStepId` 字段。每个步骤都必须明确配置三个分支的跳转逻辑。

## 分支配置要求

### 必须配置的字段

每个步骤都必须配置以下三个分支字段之一：

**新字段名称（推荐）：**
```json
{
  "perfectMatchNextStepId": "step_id",    // 完全匹配分支
  "partialMatchNextStepId": "step_id",    // 部分匹配分支
  "noMatchNextStepId": "step_id"          // 完全不匹配分支
}
```

**兼容旧字段名称：**
```json
{
  "exactMatchStepId": "step_id",          // 完全匹配分支
  "partialMatchStepId": "step_id",        // 部分匹配分支
  "noMatchStepId": "step_id"              // 完全不匹配分支
}
```

## 分支逻辑

### 分数阈值

- **完全匹配**: 分数 >= 90
- **部分匹配**: 分数 60-89
- **完全不匹配**: 分数 < 60

### 跳转规则

1. **有配置分支**: 根据分数跳转到对应的步骤
2. **无配置分支**: 教学结束
3. **步骤不存在**: 教学结束

## 场景设计模式

### 模式1: 循环学习

```json
{
  "step_1": {
    "stepName": "基础学习",
    "exactMatchStepId": "step_2_advanced",    // 完全匹配 → 高级学习
    "partialMatchStepId": "step_2_normal",    // 部分匹配 → 普通学习
    "noMatchStepId": "step_1_retry"           // 不匹配 → 重试基础
  },
  "step_2_advanced": {
    "stepName": "高级学习",
    "exactMatchStepId": "step_3_expert",      // 完全匹配 → 专家级
    "partialMatchStepId": "step_2_normal",    // 部分匹配 → 普通学习
    "noMatchStepId": "step_1_retry"           // 不匹配 → 重试基础
  },
  "step_1_retry": {
    "stepName": "重试基础",
    "exactMatchStepId": "step_2_normal",      // 完全匹配 → 普通学习
    "partialMatchStepId": "step_1_retry",     // 部分匹配 → 继续重试
    "noMatchStepId": "step_1_retry"           // 不匹配 → 继续重试
  }
}
```

### 模式2: 线性学习

```json
{
  "step_1": {
    "stepName": "学习喝水表达",
    "exactMatchStepId": "step_2",             // 完全匹配 → 下一步
    "partialMatchStepId": "step_2",           // 部分匹配 → 下一步
    "noMatchStepId": "step_1"                 // 不匹配 → 重试
  },
  "step_2": {
    "stepName": "学习吃饭表达",
    "exactMatchStepId": "step_3",             // 完全匹配 → 下一步
    "partialMatchStepId": "step_3",           // 部分匹配 → 下一步
    "noMatchStepId": "step_2"                 // 不匹配 → 重试
  },
  "step_3": {
    "stepName": "学习结束",
    // 最后一个步骤，所有分支都指向自己或结束
    "exactMatchStepId": "step_3",
    "partialMatchStepId": "step_3",
    "noMatchStepId": "step_3"
  }
}
```

### 模式3: 分层教学

```json
{
  "step_1": {
    "stepName": "基础评估",
    "exactMatchStepId": "step_advanced",      // 完全匹配 → 高级内容
    "partialMatchStepId": "step_normal",      // 部分匹配 → 普通内容
    "noMatchStepId": "step_basic"             // 不匹配 → 基础内容
  },
  "step_advanced": {
    "stepName": "高级内容",
    "exactMatchStepId": "step_expert",        // 完全匹配 → 专家内容
    "partialMatchStepId": "step_normal",      // 部分匹配 → 普通内容
    "noMatchStepId": "step_basic"             // 不匹配 → 基础内容
  },
  "step_normal": {
    "stepName": "普通内容",
    "exactMatchStepId": "step_advanced",      // 完全匹配 → 高级内容
    "partialMatchStepId": "step_normal",      // 部分匹配 → 继续普通
    "noMatchStepId": "step_basic"             // 不匹配 → 基础内容
  },
  "step_basic": {
    "stepName": "基础内容",
    "exactMatchStepId": "step_normal",        // 完全匹配 → 普通内容
    "partialMatchStepId": "step_basic",       // 部分匹配 → 继续基础
    "noMatchStepId": "step_basic"             // 不匹配 → 继续基础
  }
}
```

## 配置建议

### 1. 必须配置所有分支

```json
{
  "stepId": "step_1",
  "stepName": "问候步骤",
  "aiMessage": "你好，{childName}！",
  "expectedKeywords": "[\"你好\", \"准备好了\"]",
  "successCondition": "partial",
  "timeoutSeconds": 20,
  
  // 必须配置所有三个分支
  "exactMatchStepId": "step_2_advanced",
  "partialMatchStepId": "step_2_normal",
  "noMatchStepId": "step_1_retry"
}
```

### 2. 避免无限循环

```json
// ❌ 错误配置 - 可能导致无限循环
{
  "step_1": {
    "exactMatchStepId": "step_1",    // 完全匹配跳回自己
    "partialMatchStepId": "step_1",  // 部分匹配跳回自己
    "noMatchStepId": "step_1"        // 不匹配跳回自己
  }
}

// ✅ 正确配置 - 有退出条件
{
  "step_1": {
    "exactMatchStepId": "step_2",    // 完全匹配进入下一步
    "partialMatchStepId": "step_2",  // 部分匹配进入下一步
    "noMatchStepId": "step_1_retry"  // 不匹配进入重试步骤
  },
  "step_1_retry": {
    "exactMatchStepId": "step_2",    // 重试后完全匹配进入下一步
    "partialMatchStepId": "step_2",  // 重试后部分匹配进入下一步
    "noMatchStepId": "step_end"      // 重试后仍不匹配结束教学
  }
}
```

### 3. 设置合理的超时时间

```json
{
  "stepId": "step_1",
  "timeoutSeconds": 20,              // 基础步骤20秒
  "maxAttempts": 3,                  // 最多重试3次
  "exactMatchStepId": "step_2",
  "partialMatchStepId": "step_2",
  "noMatchStepId": "step_1"
}
```

## 测试验证

### 测试用例

1. **完全匹配测试**: 输入完全符合期望的内容
2. **部分匹配测试**: 输入部分符合期望的内容
3. **不匹配测试**: 输入不符合期望的内容
4. **分支跳转测试**: 验证跳转到正确的步骤
5. **教学结束测试**: 验证没有配置分支时教学结束

### 验证要点

- ✅ 所有步骤都配置了三个分支
- ✅ 分支跳转的步骤ID存在
- ✅ 没有无限循环
- ✅ 超时处理正确
- ✅ 教学结束条件明确

## 常见问题

### Q: 如果忘记配置某个分支会怎样？

A: 系统会结束教学，并记录 `completion_reason` 为 `no_branch_config`。

### Q: 可以只配置部分分支吗？

A: 可以，但建议配置所有分支以确保完整的教学流程。

### Q: 如何避免无限循环？

A: 确保至少有一个分支指向不同的步骤或结束条件。

### Q: 超时后如何处理？

A: 超时后会使用 `noMatchStepId` 进行跳转，如果没有配置则结束教学。

## 相关文档

- [成功条件分支配置更新](./SUCCESS_BRANCH_CONFIG_UPDATE.md)
- [三分支步骤配置示例](../THREE_BRANCH_CONFIG_EXAMPLE.md)
- [场景流程图](../core/scenario/SCENARIO_FLOW_DIAGRAM.md)
