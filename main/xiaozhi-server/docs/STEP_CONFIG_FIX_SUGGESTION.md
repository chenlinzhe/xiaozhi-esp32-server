# 步骤配置修复建议

## 问题分析

根据日志分析，当前步骤配置中的分支跳转字段存在问题：

### 当前步骤配置问题

**步骤1 (喝水步骤):**
```json
{
  "stepId": "STEP_20250817113746_b9960988",
  "partialMatchStepId": "1956923381677944835",  // ✅ 正确配置
  "noMatchStepId": "1956923381677944835",       // ✅ 正确配置
  "exactMatchStepId": "1956923381677944835"     // ✅ 正确配置
}
```

**步骤2 (完全匹配分支):**
```json
{
  "stepId": "STEP_20250817113746_967b3ee2",
  "partialMatchStepId": null,                   // ❌ 应该配置
  "noMatchStepId": null,                        // ❌ 应该配置
  "exactMatchStepId": "1956923381677944834"     // ✅ 正确配置
}
```

## 修复建议

### 1. 步骤2配置修复

步骤2应该配置完整的分支跳转字段：

```json
{
  "stepId": "STEP_20250817113746_967b3ee2",
  "stepName": "完全匹配分支",
  "aiMessage": "{文杰}小朋友，今天我们来学习吃饭表达，如果我们饿了，应该怎么跟妈妈说呢",
  "expectedKeywords": "[\"饿了\", \"肚肚\", \"吃\"]",
  "expectedPhrases": "[]",
  "successCondition": "partial",
  "maxAttempts": 3,
  "timeoutSeconds": 10,
  
  // 分支跳转配置
  "exactMatchStepId": "1956923381677944834",    // 完全匹配跳回步骤1
  "partialMatchStepId": "1956923381677944834",  // 部分匹配跳回步骤1
  "noMatchStepId": "1956923381677944834",       // 不匹配跳回步骤1
  
  // 或者使用新字段名称
  "perfectMatchNextStepId": "1956923381677944834",
  "partialMatchNextStepId": "1956923381677944834", 
  "noMatchNextStepId": "1956923381677944834"
}
```

### 2. 场景设计建议

#### 方案A: 循环学习模式
- 步骤1: 学习喝水表达
- 步骤2: 学习吃饭表达
- 两个步骤可以相互跳转，形成循环学习

#### 方案B: 线性学习模式
- 步骤1: 学习喝水表达
- 步骤2: 学习吃饭表达
- 步骤2完成后结束教学

#### 方案C: 分支学习模式
- 步骤1: 基础学习
- 根据表现跳转到不同难度的步骤2

## 当前系统行为

由于步骤2的 `partialMatchStepId` 为 `null`，系统会：

1. **用户输入**: "我渴了"
2. **评估结果**: 分数70，部分匹配
3. **分支跳转**: 尝试使用 `partialMatchStepId`，但为 `null`
4. **回退行为**: 按顺序进入下一步（步骤2）
5. **结果**: 正常进入步骤2，但跳转逻辑不完整

## 系统兼容性

当前系统已经支持：

✅ **字段兼容性**: 支持新旧两种字段名称
- `perfectMatchNextStepId` 或 `exactMatchStepId`
- `partialMatchNextStepId` 或 `partialMatchStepId`
- `noMatchNextStepId` 或 `noMatchStepId`

✅ **向后兼容**: 如果分支字段为 `null`，系统会按顺序执行

✅ **日志记录**: 详细记录分支跳转过程

## 建议操作

1. **立即修复**: 在管理后台更新步骤2的分支跳转配置
2. **测试验证**: 测试不同分数下的分支跳转是否正常
3. **场景优化**: 根据教学需求设计合适的分支跳转逻辑

## 相关文档

- [成功条件分支配置更新](./SUCCESS_BRANCH_CONFIG_UPDATE.md)
- [三分支步骤配置示例](../THREE_BRANCH_CONFIG_EXAMPLE.md)
