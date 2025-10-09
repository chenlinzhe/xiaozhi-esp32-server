# 步骤ID匹配问题修复总结

## 问题描述

在场景教学过程中，用户回答"渴了"后，系统评估通过（分数70），但是跳转到步骤ID `1956923381677944835` 时出现了"未找到步骤ID"的警告，导致教学直接结束。

## 问题分析

通过分析日志发现：

1. **步骤1配置**：
   - `id`: `1956923381677944834`
   - `stepId`: `STEP_20250817113746_b9960988`
   - `partialMatchStepId`: `1956923381677944835`

2. **步骤2配置**：
   - `id`: `1956923381677944835`
   - `stepId`: `STEP_20250817113746_967b3ee2`

3. **问题根源**：
   - 步骤1的 `partialMatchStepId` 指向的是步骤2的 `id` 字段值
   - 但原来的查找逻辑只匹配 `stepId` 字段
   - 导致无法找到对应的步骤，教学直接结束

## 修复方案

### 1. 改进步骤查找逻辑

修改 `_find_step_by_id` 方法，支持多种ID字段匹配：

```python
def _find_step_by_id(self, steps: List[Dict], step_id: str) -> Optional[int]:
    # 尝试多种ID字段匹配
    for i, step in enumerate(steps):
        # 匹配 stepId 字段
        if step.get("stepId") == step_id:
            return i
        # 匹配 id 字段
        if step.get("id") == step_id:
            return i
        # 匹配 stepCode 字段
        if step.get("stepCode") == step_id:
            return i
    return None
```

### 2. 添加调试日志

增加详细的调试日志，显示所有步骤的ID信息：

```python
self.logger.info("当前所有步骤的ID信息:")
for i, step in enumerate(steps):
    self.logger.info(f"  步骤{i}: id={step.get('id')}, stepId={step.get('stepId')}, stepCode={step.get('stepCode')}")
```

### 3. 添加回退机制

当找不到指定步骤时，尝试跳转到下一个步骤：

```python
if next_step_index is not None:
    session_data["current_step"] = next_step_index
else:
    # 回退到下一个步骤
    current_step_index = session_data.get("current_step", 0)
    next_step_index = current_step_index + 1
    if next_step_index < len(steps):
        session_data["current_step"] = next_step_index
```

## 修复效果

### 测试结果

通过测试脚本验证，修复后的查找逻辑能够：

1. ✅ 通过 `id` 字段查找步骤
2. ✅ 通过 `stepId` 字段查找步骤  
3. ✅ 通过 `stepCode` 字段查找步骤
4. ✅ 正确处理不存在的ID

### 实际场景

现在当用户回答"渴了"时：

1. 系统评估通过（分数70）
2. 根据 `partialMatchStepId` 配置，查找步骤ID `1956923381677944835`
3. 通过 `id` 字段成功找到步骤2（索引1）
4. 正常跳转到步骤2，继续教学流程

## 代码变更

- **文件**: `main/xiaozhi-server/core/scenario/chat_status_manager.py`
- **方法**: `_find_step_by_id`
- **行数**: 约30行代码修改

## 注意事项

1. 修复后的代码向后兼容，不会影响现有的正常流程
2. 增加了详细的调试日志，便于后续问题排查
3. 添加了回退机制，提高了系统的健壮性
4. 支持多种ID字段匹配，适应不同的配置方式

## 建议

1. 建议在场景配置时，确保ID字段的一致性
2. 可以考虑在配置验证阶段检查步骤引用的有效性
3. 定期检查日志，确保步骤跳转正常工作
