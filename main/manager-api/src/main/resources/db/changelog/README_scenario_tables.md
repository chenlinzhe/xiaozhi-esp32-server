# 场景配置表结构脚本使用说明

## 概述

`20241201_complete_scenario_tables.sql` 是一个完整的数据库脚本，包含了所有场景相关表的创建、修复和优化操作。此脚本整合了之前分散的8个脚本，确保数据库表结构与Java实体类完全匹配。

## 脚本内容

### 第一部分：创建基础表结构
- `ai_scenario` - 场景配置表
- `ai_scenario_step` - 对话步骤配置表
- `ai_child_learning_record` - 儿童学习记录表
- `ai_step_template` - 步骤模板表

### 第二部分：修复表结构问题
- 添加缺失的 `template_id` 字段到 `ai_step_template` 表
- 添加教学模式相关字段到 `ai_scenario` 表
- 添加教学模式相关字段到 `ai_scenario_step` 表
- 添加 `update_date` 字段到 `ai_child_learning_record` 表

### 第三部分：添加缺失的索引
- 为所有新增字段添加适当的索引
- 优化查询性能

### 第四部分：插入默认数据
- 插入基础的步骤模板数据

### 第五部分：创建视图
- `v_scenario_stats` - 场景统计视图
- `v_child_learning_stats` - 儿童学习统计视图

### 第六部分：验证表结构完整性
- 验证所有字段是否正确添加
- 检查数据完整性

### 第七部分：显示最终表结构信息
- 显示所有表的创建语句用于验证

## 执行方式

### 方式一：直接执行完整脚本
```sql
-- 在MySQL客户端中执行
source /path/to/20241201_complete_scenario_tables.sql;
```

### 方式二：分步执行（推荐用于生产环境）
```sql
-- 1. 先执行第一部分（创建表）
-- 2. 检查表是否创建成功
-- 3. 执行第二部分（修复字段）
-- 4. 执行第三部分（添加索引）
-- 5. 执行第四部分（插入数据）
-- 6. 执行第五部分（创建视图）
-- 7. 执行验证部分
```

## 执行前准备

### 1. 备份数据库
```sql
-- 备份现有数据
mysqldump -u username -p database_name > backup_before_scenario_tables.sql
```

### 2. 检查数据库版本
```sql
-- 确保MySQL版本支持 IF NOT EXISTS 语法
SELECT VERSION();
-- 建议使用 MySQL 5.7+ 或 MariaDB 10.2+
```

### 3. 检查权限
确保数据库用户具有以下权限：
- CREATE
- ALTER
- INSERT
- SELECT
- CREATE VIEW

## 执行后验证

### 1. 检查表是否创建成功
```sql
SHOW TABLES LIKE 'ai_%';
```

### 2. 检查字段是否添加成功
```sql
-- 检查 ai_step_template 表的 template_id 字段
DESCRIBE ai_step_template;

-- 检查 ai_scenario 表的教学模式字段
DESCRIBE ai_scenario;

-- 检查 ai_scenario_step 表的教学模式字段
DESCRIBE ai_scenario_step;
```

### 3. 检查数据是否插入成功
```sql
-- 检查默认模板数据
SELECT * FROM ai_step_template;

-- 检查视图是否创建成功
SHOW TABLES LIKE 'v_%';
```

### 4. 验证表结构完整性
执行脚本中的验证查询，确保所有字段都正确添加。

## 常见问题解决

### 问题1：字段已存在错误
如果遇到 "Duplicate column name" 错误，说明字段已经存在，可以忽略此错误。

### 问题2：索引已存在错误
如果遇到 "Duplicate key name" 错误，说明索引已经存在，可以忽略此错误。

### 问题3：权限不足
确保数据库用户具有足够的权限执行所有操作。

### 问题4：字符集问题
脚本使用 `utf8mb4` 字符集，确保数据库支持此字符集。

## 回滚方案

如果需要回滚更改，可以执行以下操作：

### 1. 删除视图
```sql
DROP VIEW IF EXISTS v_scenario_stats;
DROP VIEW IF EXISTS v_child_learning_stats;
```

### 2. 删除表（谨慎操作）
```sql
DROP TABLE IF EXISTS ai_step_template;
DROP TABLE IF EXISTS ai_child_learning_record;
DROP TABLE IF EXISTS ai_scenario_step;
DROP TABLE IF EXISTS ai_scenario;
```

### 3. 恢复备份
```sql
-- 使用之前创建的备份文件恢复
mysql -u username -p database_name < backup_before_scenario_tables.sql
```

## 注意事项

1. **生产环境执行前务必备份数据库**
2. **建议在测试环境先执行验证**
3. **执行后重启应用程序以确保所有更改生效**
4. **检查应用程序日志确认没有数据库相关错误**
5. **验证所有场景相关功能正常工作**

## 联系支持

如果在执行过程中遇到问题，请：
1. 检查错误日志
2. 确认数据库版本和权限
3. 参考本文档的常见问题解决部分
4. 联系技术支持团队

---

**脚本版本**: 20241201_complete_scenario_tables.sql  
**创建时间**: 2024-12-01  
**适用版本**: MySQL 5.7+, MariaDB 10.2+
