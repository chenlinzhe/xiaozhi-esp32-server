-- 数据库修复脚本 - 修复ai_message字段没有默认值的问题
-- =====================================================
-- 创建时间：2025-09-16
-- 描述：修复ai_message字段没有默认值导致的插入错误
-- 问题：删除AI消息字段后，数据库中的ai_message字段仍然存在且没有默认值
-- =====================================================

-- =====================================================
-- 第一部分：修复ai_message字段的默认值
-- =====================================================

-- 为ai_message字段添加默认值
ALTER TABLE `ai_scenario_step` 
MODIFY COLUMN `ai_message` text DEFAULT NULL COMMENT 'AI消息内容（已废弃，保留用于兼容性）';

-- 为ai_step_template表的ai_message字段添加默认值
ALTER TABLE `ai_step_template` 
MODIFY COLUMN `ai_message` text DEFAULT NULL COMMENT 'AI消息内容（已废弃，保留用于兼容性）';

-- =====================================================
-- 第二部分：检查其他可能受影响的字段
-- =====================================================

-- 检查alternative_message字段
ALTER TABLE `ai_scenario_step` 
MODIFY COLUMN `alternative_message` text DEFAULT NULL COMMENT '替代消息（已废弃，保留用于兼容性）';

-- 检查praise_message字段
ALTER TABLE `ai_scenario_step` 
MODIFY COLUMN `praise_message` text DEFAULT NULL COMMENT '夸奖消息（已废弃，保留用于兼容性）';

-- 检查encouragement_message字段
ALTER TABLE `ai_scenario_step` 
MODIFY COLUMN `encouragement_message` text DEFAULT NULL COMMENT '鼓励消息（已废弃，保留用于兼容性）';

-- 检查ai_step_template表的alternative_message字段
ALTER TABLE `ai_step_template` 
MODIFY COLUMN `alternative_message` text DEFAULT NULL COMMENT '替代消息（已废弃，保留用于兼容性）';

-- =====================================================
-- 第三部分：验证表结构
-- =====================================================

-- 验证ai_scenario_step表结构
DESCRIBE ai_scenario_step;

-- 验证ai_step_template表结构
DESCRIBE ai_step_template;

-- 检查字段的默认值设置
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME IN ('ai_scenario_step', 'ai_step_template')
AND COLUMN_NAME IN ('ai_message', 'alternative_message', 'praise_message', 'encouragement_message')
ORDER BY TABLE_NAME, COLUMN_NAME;

-- =====================================================
-- 第四部分：测试插入操作
-- =====================================================

-- 测试插入操作（使用事务，可以回滚）
START TRANSACTION;

-- 测试插入一个步骤记录
INSERT INTO ai_scenario_step (
    step_id, scenario_id, step_code, step_name, step_order, 
    use_message_list, expected_keywords, expected_phrases, 
    max_attempts, timeout_seconds, success_condition, speech_rate,
    exact_match_step_id, partial_match_step_id, no_match_step_id,
    next_step_id, retry_step_id, wait_time_seconds, gesture_hint, 
    music_effect, is_optional, step_type, creator, create_date
) VALUES (
    'TEST_STEP_001', 'TEST_SCENARIO_001', 'TEST_CODE', '测试步骤', 1,
    1, '[]', '[]', 3, 10, 'partial', 1.0,
    NULL, NULL, NULL, NULL, NULL, 10, NULL, NULL, 0, 'normal', 1, NOW()
);

-- 检查插入结果
SELECT step_id, step_name, ai_message, alternative_message, praise_message, encouragement_message
FROM ai_scenario_step 
WHERE step_id = 'TEST_STEP_001';

-- 回滚测试数据
ROLLBACK;

-- =====================================================
-- 第五部分：清理现有数据中的空值
-- =====================================================

-- 将现有的空字符串设置为NULL
UPDATE ai_scenario_step 
SET ai_message = NULL 
WHERE ai_message = '';

UPDATE ai_scenario_step 
SET alternative_message = NULL 
WHERE alternative_message = '';

UPDATE ai_scenario_step 
SET praise_message = NULL 
WHERE praise_message = '';

UPDATE ai_scenario_step 
SET encouragement_message = NULL 
WHERE encouragement_message = '';

-- 清理ai_step_template表
UPDATE ai_step_template 
SET ai_message = NULL 
WHERE ai_message = '';

UPDATE ai_step_template 
SET alternative_message = NULL 
WHERE alternative_message = '';

-- =====================================================
-- 脚本执行完成
-- =====================================================
-- 此脚本实现了以下功能：
-- 1. 为ai_message字段添加了默认值NULL
-- 2. 为其他废弃字段添加了默认值NULL
-- 3. 验证了表结构的正确性
-- 4. 测试了插入操作
-- 5. 清理了现有数据中的空字符串
-- 
-- 修复后的效果：
-- - 插入步骤时不再需要提供ai_message等废弃字段的值
-- - 数据库操作不会因为缺少默认值而失败
-- - 保持了向后兼容性
-- 
-- 建议在执行后重启Spring Boot应用程序以确保更改生效
