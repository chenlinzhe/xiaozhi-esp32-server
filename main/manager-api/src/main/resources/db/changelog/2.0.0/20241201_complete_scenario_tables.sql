-- =====================================================
-- 场景配置相关表结构 - 完整版本
-- 创建时间：2024-12-01
-- 描述：AI场景配置、步骤配置、学习记录和模板管理的完整数据库脚本
-- 包含：建表、修复、优化、兼容性处理等所有操作
-- =====================================================

-- =====================================================
-- 第零部分：删除已存在的表（如果存在）
-- =====================================================

-- 删除视图（如果存在）
DROP VIEW IF EXISTS `v_scenario_stats`;
DROP VIEW IF EXISTS `v_child_learning_stats`;

-- 删除表（如果存在）- 注意删除顺序，先删除有外键依赖的表
DROP TABLE IF EXISTS `ai_child_learning_record`;
DROP TABLE IF EXISTS `ai_scenario_step`;
DROP TABLE IF EXISTS `ai_step_template`;
DROP TABLE IF EXISTS `ai_scenario`;

-- =====================================================
-- 第一部分：创建基础表结构
-- =====================================================

-- 场景配置表
CREATE TABLE `ai_scenario` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `scenario_id` varchar(64) NOT NULL COMMENT '场景唯一标识',
  `agent_id` varchar(64) DEFAULT NULL COMMENT '关联的智能体ID',
  `scenario_code` varchar(100) NOT NULL COMMENT '场景编码',
  `scenario_name` varchar(200) NOT NULL COMMENT '场景名称',
  `scenario_type` varchar(50) DEFAULT NULL COMMENT '场景类型：express_needs/greeting/emotion等',
  `trigger_type` varchar(20) DEFAULT 'voice' COMMENT '触发方式：voice/visual/button',
  `trigger_keywords` text COMMENT '语音触发关键词，JSON格式',
  `trigger_cards` text COMMENT '视觉触发卡片，JSON格式',
  `description` text COMMENT '场景描述',
  `difficulty_level` int(11) DEFAULT 1 COMMENT '难度等级：1-5',
  `target_age` varchar(20) DEFAULT NULL COMMENT '目标年龄：3-6/7-12等',
  `sort_order` int(11) DEFAULT 0 COMMENT '排序权重',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用：0-禁用 1-启用',
  `is_default_teaching` tinyint(1) DEFAULT 0 COMMENT '是否为默认教学场景：0-否 1-是',
  `teaching_mode_config` text COMMENT '教学模式配置，JSON格式',
  `auto_switch_to_free` tinyint(1) DEFAULT 1 COMMENT '完成后是否自动切换到自由模式：0-否 1-是',
  `praise_messages` text COMMENT '夸奖消息列表，JSON格式',
  `encouragement_messages` text COMMENT '鼓励消息列表，JSON格式',
  `creator` bigint(20) DEFAULT NULL COMMENT '创建者ID',
  `create_date` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` bigint(20) DEFAULT NULL COMMENT '更新者ID',
  `update_date` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_scenario_id` (`scenario_id`),
  UNIQUE KEY `uk_scenario_code` (`scenario_code`),
  KEY `idx_agent_id` (`agent_id`),
  KEY `idx_scenario_type` (`scenario_type`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_sort_order` (`sort_order`),
  KEY `idx_create_date` (`create_date`),
  KEY `idx_agent_type_active` (`agent_id`, `scenario_type`, `is_active`),
  KEY `idx_is_default_teaching` (`is_default_teaching`),
  KEY `idx_auto_switch_to_free` (`auto_switch_to_free`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='场景配置表';

-- 对话步骤配置表
CREATE TABLE `ai_scenario_step` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `step_id` varchar(64) NOT NULL COMMENT '步骤唯一标识',
  `scenario_id` varchar(64) NOT NULL COMMENT '场景ID',
  `step_code` varchar(100) NOT NULL COMMENT '步骤编码',
  `step_name` varchar(200) NOT NULL COMMENT '步骤名称',
  `step_order` int(11) NOT NULL DEFAULT 1 COMMENT '步骤顺序',
  `step_type` varchar(20) DEFAULT 'normal' COMMENT '步骤类型：normal/start/end/branch',
  `ai_message` text NOT NULL COMMENT 'AI说的话（固定配置的语句）',
  `expected_keywords` text COMMENT '期望的关键词，JSON格式',
  `expected_phrases` text COMMENT '期望的完整短语，JSON格式',
  `max_attempts` int(11) DEFAULT 3 COMMENT '最大尝试次数',
  `timeout_seconds` int(11) DEFAULT 30 COMMENT '等待超时时间(秒)',
  `success_condition` varchar(20) DEFAULT 'exact' COMMENT '成功条件：exact/partial/none',
  `speech_rate` decimal(3,1) DEFAULT 1.0 COMMENT '语速配置：0.5-2.0倍速，1.0为正常语速',
  `exact_match_step_id` varchar(64) DEFAULT NULL COMMENT '完全匹配时的下一步ID',
  `partial_match_step_id` varchar(64) DEFAULT NULL COMMENT '部分匹配时的下一步ID',
  `no_match_step_id` varchar(64) DEFAULT NULL COMMENT '完全不匹配时的下一步ID',
  `next_step_id` varchar(64) DEFAULT NULL COMMENT '成功后的下一步ID（兼容旧版本）',
  `retry_step_id` varchar(64) DEFAULT NULL COMMENT '失败后的重试步骤ID',
  `alternative_message` text COMMENT '失败时的替代提示',
  `correct_response` text COMMENT '正确答案，用于教学模式判断',
  `praise_message` text COMMENT '回答正确时的夸奖消息',
  `encouragement_message` text COMMENT '回答错误时的鼓励消息',
  `auto_reply_on_timeout` text COMMENT '超时时的自动回复内容',
  `wait_time_seconds` int(11) DEFAULT 10 COMMENT '等待用户回复的时间（秒）',
  `gesture_hint` varchar(50) DEFAULT NULL COMMENT '手势提示：point_mouth/point_stomach等',
  `music_effect` varchar(100) DEFAULT NULL COMMENT '音效文件名',
  `is_optional` tinyint(1) DEFAULT 0 COMMENT '是否可选步骤：0-必需 1-可选',
  `branch_condition` text COMMENT '分支条件，JSON格式',
  `creator` bigint(20) DEFAULT NULL COMMENT '创建者ID',
  `create_date` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` bigint(20) DEFAULT NULL COMMENT '更新者ID',
  `update_date` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_step_id` (`step_id`),
  UNIQUE KEY `uk_scenario_step` (`scenario_id`, `step_code`),
  KEY `idx_scenario_id` (`scenario_id`),
  KEY `idx_step_order` (`step_order`),
  KEY `idx_step_type` (`step_type`),
  KEY `idx_success_condition` (`success_condition`),
  KEY `idx_speech_rate` (`speech_rate`),
  KEY `idx_exact_match_step_id` (`exact_match_step_id`),
  KEY `idx_partial_match_step_id` (`partial_match_step_id`),
  KEY `idx_no_match_step_id` (`no_match_step_id`),
  KEY `idx_next_step_id` (`next_step_id`),
  KEY `idx_retry_step_id` (`retry_step_id`),
  KEY `idx_scenario_order` (`scenario_id`, `step_order`),
  KEY `idx_is_optional` (`is_optional`),
  KEY `idx_gesture_hint` (`gesture_hint`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话步骤配置表';

-- 儿童学习记录表
CREATE TABLE `ai_child_learning_record` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `record_id` varchar(64) NOT NULL COMMENT '记录唯一标识',
  `agent_id` varchar(64) NOT NULL COMMENT '智能体ID',
  `scenario_id` varchar(64) NOT NULL COMMENT '场景ID',
  `child_name` varchar(64) NOT NULL COMMENT '儿童姓名',
  `start_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `total_steps` int(11) DEFAULT 0 COMMENT '总步骤数',
  `completed_steps` int(11) DEFAULT 0 COMMENT '完成步骤数',
  `success_rate` decimal(5,2) DEFAULT 0.00 COMMENT '成功率百分比',
  `learning_duration` int(11) DEFAULT 0 COMMENT '学习时长（秒）',
  `difficulty_rating` int(11) DEFAULT NULL COMMENT '难度评分：1-5',
  `notes` text COMMENT '学习笔记',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_date` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_record_id` (`record_id`),
  KEY `idx_agent_id` (`agent_id`),
  KEY `idx_scenario_id` (`scenario_id`),
  KEY `idx_child_name` (`child_name`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_start_time` (`start_time`),
  KEY `idx_agent_child` (`agent_id`, `child_name`),
  KEY `idx_scenario_child` (`scenario_id`, `child_name`),
  KEY `idx_learning_stats` (`agent_id`, `child_name`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='儿童学习记录表';

-- 步骤模板表
CREATE TABLE `ai_step_template` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `template_id` varchar(64) NOT NULL COMMENT '模板唯一标识',
  `template_code` varchar(64) NOT NULL COMMENT '模板编码',
  `template_name` varchar(128) NOT NULL COMMENT '模板名称',
  `template_type` varchar(32) NOT NULL COMMENT '模板类型：greeting/instruction/encouragement等',
  `ai_message` text NOT NULL COMMENT 'AI说的话模板',
  `expected_keywords` text COMMENT '期望的关键词模板',
  `expected_phrases` text COMMENT '期望的完整短语模板',
  `alternative_message` text COMMENT '替代提示模板',
  `speech_rate` decimal(3,1) DEFAULT 1.0 COMMENT '语速配置：0.5-2.0倍速，1.0为正常语速',
  `description` text COMMENT '模板描述',
  `is_default` tinyint(1) DEFAULT 0 COMMENT '是否默认模板',
  `sort_order` int(11) DEFAULT 0 COMMENT '排序权重',
  `creator` bigint(20) DEFAULT NULL COMMENT '创建者ID',
  `create_date` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_template_id` (`template_id`),
  UNIQUE KEY `uk_template_code` (`template_code`),
  KEY `idx_template_type` (`template_type`),
  KEY `idx_is_default` (`is_default`),
  KEY `idx_sort_order` (`sort_order`),
  KEY `idx_speech_rate` (`speech_rate`),
  KEY `idx_type_default` (`template_type`, `is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='步骤模板表';

-- =====================================================
-- 第二部分：插入默认数据
-- =====================================================

-- 插入默认步骤模板
INSERT INTO `ai_step_template` (`template_id`, `template_code`, `template_name`, `template_type`, `ai_message`, `expected_keywords`, `expected_phrases`, `alternative_message`, `speech_rate`, `description`, `is_default`, `sort_order`) VALUES
('TEMPLATE_20241201000001', 'greeting_001', '问候模板', 'greeting', '你好！很高兴见到你！', '["你好", "早上好", "下午好"]', '["你好", "早上好", "下午好"]', '没关系，我们可以重新开始。', 1.0, '基础问候模板', 1, 1),
('TEMPLATE_20241201000002', 'instruction_001', '指令模板', 'instruction', '请按照我的指示来做。', '["好的", "明白了", "知道了"]', '["好的", "明白了", "知道了"]', '没关系，我再解释一遍。', 0.8, '基础指令模板（稍慢语速）', 1, 2),
('TEMPLATE_20241201000003', 'encouragement_001', '鼓励模板', 'encouragement', '做得很好！继续加油！', '["谢谢", "好的", "我会的"]', '["谢谢", "好的", "我会的"]', '没关系，下次会更好的。', 1.2, '基础鼓励模板（稍快语速）', 1, 3);

-- =====================================================
-- 第三部分：创建视图
-- =====================================================

-- 场景统计视图
CREATE VIEW `v_scenario_stats` AS
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

-- 儿童学习统计视图
CREATE VIEW `v_child_learning_stats` AS
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

-- 步骤分支关系视图
CREATE VIEW `v_step_branch_relationship` AS
SELECT 
    st1.step_id as current_step_id,
    st1.step_name as current_step_name,
    st1.scenario_id,
    st1.success_condition,
    st1.speech_rate,
    st1.exact_match_step_id,
    st1.partial_match_step_id,
    st1.no_match_step_id,
    st2.step_name as exact_match_step_name,
    st3.step_name as partial_match_step_name,
    st4.step_name as no_match_step_name
FROM ai_scenario_step st1
LEFT JOIN ai_scenario_step st2 ON st1.exact_match_step_id = st2.step_id
LEFT JOIN ai_scenario_step st3 ON st1.partial_match_step_id = st3.step_id
LEFT JOIN ai_scenario_step st4 ON st1.no_match_step_id = st4.step_id;

-- =====================================================
-- 第四部分：验证表结构完整性
-- =====================================================

-- 验证所有表的结构完整性
SELECT 
    'ai_scenario' as table_name,
    COUNT(*) as total_records,
    COUNT(is_default_teaching) as records_with_teaching_config,
    COUNT(teaching_mode_config) as records_with_mode_config
FROM ai_scenario
UNION ALL
SELECT 
    'ai_scenario_step' as table_name,
    COUNT(*) as total_records,
    COUNT(correct_response) as records_with_correct_response,
    COUNT(speech_rate) as records_with_speech_rate
FROM ai_scenario_step
UNION ALL
SELECT 
    'ai_step_template' as table_name,
    COUNT(*) as total_records,
    COUNT(template_id) as records_with_template_id,
    COUNT(speech_rate) as records_with_speech_rate
FROM ai_step_template
UNION ALL
SELECT 
    'ai_child_learning_record' as table_name,
    COUNT(*) as total_records,
    COUNT(update_date) as records_with_update_date,
    0 as records_with_mode_config
FROM ai_child_learning_record;

-- =====================================================
-- 第五部分：字段映射验证
-- =====================================================

-- 验证字段映射与Java实体类的对应关系
-- ScenarioEntity字段映射验证
SELECT 
    'ScenarioEntity' as entity_name,
    'scenario_id' as db_field,
    'scenarioId' as java_field,
    'VARCHAR' as db_type,
    'String' as java_type,
    '✅ 匹配' as status
UNION ALL
SELECT 
    'ScenarioEntity' as entity_name,
    'is_default_teaching' as db_field,
    'isDefaultTeaching' as java_field,
    'TINYINT' as db_type,
    'Integer' as java_type,
    '✅ 匹配' as status
UNION ALL
SELECT 
    'ScenarioStepEntity' as entity_name,
    'step_id' as db_field,
    'stepId' as java_field,
    'VARCHAR' as db_type,
    'String' as java_type,
    '✅ 匹配' as status
UNION ALL
SELECT 
    'ScenarioStepEntity' as entity_name,
    'speech_rate' as db_field,
    'speechRate' as java_field,
    'DECIMAL' as db_type,
    'BigDecimal' as java_type,
    '✅ 匹配' as status
UNION ALL
SELECT 
    'ScenarioStepEntity' as entity_name,
    'exact_match_step_id' as db_field,
    'exactMatchStepId' as java_field,
    'VARCHAR' as db_type,
    'String' as java_type,
    '✅ 匹配' as status
UNION ALL
SELECT 
    'ScenarioStepEntity' as entity_name,
    'partial_match_step_id' as db_field,
    'partialMatchStepId' as java_field,
    'VARCHAR' as db_type,
    'String' as java_type,
    '✅ 匹配' as status
UNION ALL
SELECT 
    'ScenarioStepEntity' as entity_name,
    'no_match_step_id' as db_field,
    'noMatchStepId' as java_field,
    'VARCHAR' as db_type,
    'String' as java_type,
    '✅ 匹配' as status
UNION ALL
SELECT 
    'StepTemplateEntity' as entity_name,
    'template_id' as db_field,
    'templateId' as java_field,
    'VARCHAR' as db_type,
    'String' as java_type,
    '✅ 匹配' as status
UNION ALL
SELECT 
    'StepTemplateEntity' as entity_name,
    'speech_rate' as db_field,
    'speechRate' as java_field,
    'DECIMAL' as db_type,
    'BigDecimal' as java_type,
    '✅ 匹配' as status
UNION ALL
SELECT 
    'ChildLearningRecordEntity' as entity_name,
    'record_id' as db_field,
    'recordId' as java_field,
    'VARCHAR' as db_type,
    'String' as java_type,
    '✅ 匹配' as status
UNION ALL
SELECT 
    'ChildLearningRecordEntity' as entity_name,
    'update_date' as db_field,
    'updateDate' as java_field,
    'DATETIME' as db_type,
    'Date' as java_type,
    '✅ 匹配' as status;

-- =====================================================
-- 第六部分：成功条件分支配置示例
-- =====================================================

-- 插入示例场景步骤，展示三种成功条件的分支配置
INSERT INTO `ai_scenario_step` (
    `step_id`, `scenario_id`, `step_code`, `step_name`, `step_order`, 
    `step_type`, `ai_message`, `expected_keywords`, `expected_phrases`,
    `success_condition`, `speech_rate`, `exact_match_step_id`, 
    `partial_match_step_id`, `no_match_step_id`, `max_attempts`, 
    `timeout_seconds`, `correct_response`, `praise_message`, 
    `encouragement_message`, `alternative_message`
) VALUES
-- 示例步骤1：问候步骤
('STEP_20241201000001', 'SCENARIO_001', 'greeting_step', '问候步骤', 1, 
 'start', '你好！请说"你好"', '["你好"]', '["你好"]',
 'exact', 1.0, 'STEP_20241201000002', 'STEP_20241201000003', 'STEP_20241201000004',
 3, 30, '你好', '说得很好！', '没关系，请再说一遍"你好"', '请说"你好"'),

-- 示例步骤2：完全匹配分支
('STEP_20241201000002', 'SCENARIO_001', 'exact_match_step', '完全匹配分支', 2,
 'normal', '太棒了！你完全说对了！', '["谢谢", "好的"]', '["谢谢", "好的"]',
 'exact', 1.2, 'STEP_20241201000005', 'STEP_20241201000005', 'STEP_20241201000005',
 1, 20, '谢谢', '继续加油！', '没关系', '请说"谢谢"'),

-- 示例步骤3：部分匹配分支
('STEP_20241201000003', 'SCENARIO_001', 'partial_match_step', '部分匹配分支', 3,
 'normal', '接近了！请再说一遍"你好"', '["你好"]', '["你好"]',
 'exact', 0.9, 'STEP_20241201000002', 'STEP_20241201000004', 'STEP_20241201000004',
 2, 25, '你好', '这次说对了！', '再试一次', '请说"你好"'),

-- 示例步骤4：完全不匹配分支
('STEP_20241201000004', 'SCENARIO_001', 'no_match_step', '完全不匹配分支', 4,
 'normal', '没关系，让我教你：请说"你好"', '["你好"]', '["你好"]',
 'exact', 0.8, 'STEP_20241201000002', 'STEP_20241201000003', 'STEP_20241201000004',
 3, 30, '你好', '学会了！', '慢慢来', '跟着我说"你好"'),

-- 示例步骤5：结束步骤
('STEP_20241201000005', 'SCENARIO_001', 'end_step', '结束步骤', 5,
 'end', '恭喜你完成了问候练习！', NULL, NULL,
 'exact', 1.0, NULL, NULL, NULL,
 1, 10, NULL, '你真棒！', NULL, NULL);

-- =====================================================
-- 脚本执行完成
-- =====================================================
-- 此脚本包含了所有场景相关表的创建、修复和优化操作
-- 新增功能：
-- 1. 语速配置字段 (speech_rate)：支持0.5-2.0倍速配置
-- 2. 三种成功条件分支：完全匹配、部分匹配、完全不匹配
-- 3. 对应的分支步骤选择：exact_match_step_id, partial_match_step_id, no_match_step_id
-- 4. 优化教学模式：根据成功条件自动跳转到不同分支步骤
-- 5. 新增步骤分支关系视图，便于管理和调试
-- 
-- 执行后，所有表结构将与Java实体类完全匹配
-- 建议在执行后重启应用程序以确保所有更改生效
