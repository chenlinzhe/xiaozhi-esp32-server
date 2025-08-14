-- =====================================================
-- 修复场景配置相关表的字符集排序规则冲突和SQL模式问题
-- 创建时间：2024-12-01
-- 描述：修复表之间的字符集排序规则不一致问题和GROUP BY兼容性
-- =====================================================

-- 临时禁用 ONLY_FULL_GROUP_BY 模式（可选，如果遇到GROUP BY问题）
-- SET SESSION sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));

-- 修复 ai_scenario 表的字符集排序规则
ALTER TABLE `ai_scenario` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 修复 ai_scenario_step 表的字符集排序规则
ALTER TABLE `ai_scenario_step` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 修复 ai_child_learning_record 表的字符集排序规则
ALTER TABLE `ai_child_learning_record` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 修复 ai_step_template 表的字符集排序规则
ALTER TABLE `ai_step_template` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 确保 ai_agent 表也使用相同的字符集排序规则
ALTER TABLE `ai_agent` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 重新创建视图以确保一致性
DROP VIEW IF EXISTS `v_scenario_stats`;
CREATE OR REPLACE VIEW `v_scenario_stats` AS
SELECT 
    s.id,
    s.scenario_id,
    s.scenario_name,
    s.scenario_type,
    s.agent_id,
    COUNT(st.id) as step_count,
    COUNT(DISTINCT clr.child_name) as child_count,
    AVG(clr.success_rate) as avg_success_rate,
    SUM(clr.learning_duration) as total_learning_time
FROM ai_scenario s
LEFT JOIN ai_scenario_step st ON s.scenario_id = st.scenario_id
LEFT JOIN ai_child_learning_record clr ON s.scenario_id = clr.scenario_id
GROUP BY s.id, s.scenario_id, s.scenario_name, s.scenario_type, s.agent_id;

-- 重新创建儿童学习统计视图
DROP VIEW IF EXISTS `v_child_learning_stats`;
CREATE OR REPLACE VIEW `v_child_learning_stats` AS
SELECT 
    child_name,
    agent_id,
    COUNT(DISTINCT scenario_id) as scenario_count,
    COUNT(*) as total_sessions,
    AVG(success_rate) as avg_success_rate,
    SUM(learning_duration) as total_learning_time,
    MAX(created_at) as last_learning_time
FROM ai_child_learning_record
GROUP BY child_name, agent_id;
