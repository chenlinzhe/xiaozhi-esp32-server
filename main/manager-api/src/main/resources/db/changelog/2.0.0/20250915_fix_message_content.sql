-- 数据修复脚本 - 修复消息内容中的儿童姓名重复问题
-- =====================================================
-- 创建时间：2025-09-15
-- 描述：修复迁移后的消息内容中儿童姓名重复的问题
-- 问题：消息内容中既有{文杰}占位符，又有实际的儿童姓名，导致替换后重复
-- =====================================================

-- =====================================================
-- 第一部分：修复消息内容中的儿童姓名重复问题
-- =====================================================

-- 修复包含"小朋友"的消息内容
UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '小朋友小朋友', '{childName}小朋友')
WHERE message_content LIKE '%小朋友小朋友%'
AND parameters LIKE '%"migrated": true%';

-- 修复包含"文杰"的消息内容
UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '文杰小朋友', '{childName}小朋友')
WHERE message_content LIKE '%文杰小朋友%'
AND parameters LIKE '%"migrated": true%';

-- 修复包含"小明"的消息内容
UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '小明小朋友', '{childName}小朋友')
WHERE message_content LIKE '%小明小朋友%'
AND parameters LIKE '%"migrated": true%';

-- 修复包含"小红"的消息内容
UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '小红小朋友', '{childName}小朋友')
WHERE message_content LIKE '%小红小朋友%'
AND parameters LIKE '%"migrated": true%';

-- 修复包含"小华"的消息内容
UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '小华小朋友', '{childName}小朋友')
WHERE message_content LIKE '%小华小朋友%'
AND parameters LIKE '%"migrated": true%';

-- =====================================================
-- 第二部分：统一占位符格式
-- =====================================================

-- 将{文杰}统一替换为{childName}
UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '{文杰}', '{childName}')
WHERE message_content LIKE '%{文杰}%'
AND parameters LIKE '%"migrated": true%';

-- =====================================================
-- 第三部分：验证修复结果
-- =====================================================

-- 查看修复后的消息内容
SELECT 
    message_id,
    step_id,
    message_content,
    parameters
FROM ai_step_message 
WHERE parameters LIKE '%"migrated": true%'
ORDER BY step_id, message_order;

-- 检查是否还有重复的儿童姓名
SELECT 
    message_id,
    step_id,
    message_content
FROM ai_step_message 
WHERE (
    message_content LIKE '%小朋友小朋友%' OR
    message_content LIKE '%文杰小朋友%' OR
    message_content LIKE '%小明小朋友%' OR
    message_content LIKE '%小红小朋友%' OR
    message_content LIKE '%小华小朋友%'
)
AND parameters LIKE '%"migrated": true%';

-- =====================================================
-- 第四部分：更新修复标记
-- =====================================================

-- 更新修复标记
UPDATE ai_step_message 
SET parameters = JSON_SET(parameters, '$.content_fixed', true, '$.fix_date', NOW())
WHERE parameters LIKE '%"migrated": true%'
AND parameters NOT LIKE '%"content_fixed": true%';

-- =====================================================
-- 脚本执行完成
-- =====================================================
-- 此脚本实现了以下功能：
-- 1. 修复了消息内容中儿童姓名重复的问题
-- 2. 统一了占位符格式，使用{childName}替代{文杰}
-- 3. 验证了修复结果
-- 4. 更新了修复标记
-- 
-- 修复后的效果：
-- - 消息内容不再包含重复的儿童姓名
-- - 统一使用{childName}占位符
-- - 替换时不会出现重复问题
-- 
-- 建议在执行后重启应用程序以确保更改生效
