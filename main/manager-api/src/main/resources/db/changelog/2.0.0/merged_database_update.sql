-- =====================================================
-- 数据库更新脚本 - 2.0.0版本合并版
-- 创建时间：2025-01-20
-- 描述：合并所有2.0.0版本的数据库更新，包含场景配置、用户信息、AI消息列表等功能
-- 注意：此脚本包含所有必要的表创建、字段添加、索引创建和数据迁移
-- =====================================================

-- =====================================================
-- 第一部分：删除已存在的表（如果存在）
-- =====================================================

-- 删除视图（如果存在）
DROP VIEW IF EXISTS `v_scenario_stats`;
DROP VIEW IF EXISTS `v_child_learning_stats`;
DROP VIEW IF EXISTS `v_step_branch_relationship`;

-- 删除表（如果存在）- 注意删除顺序，先删除有外键依赖的表
DROP TABLE IF EXISTS `ai_child_learning_record`;
DROP TABLE IF EXISTS `ai_scenario_step`;
DROP TABLE IF EXISTS `ai_step_template`;
DROP TABLE IF EXISTS `ai_scenario`;
DROP TABLE IF EXISTS `ai_step_message`;
DROP TABLE IF EXISTS `user_info`;
DROP TABLE IF EXISTS `user_interaction_log`;

-- =====================================================
-- 第二部分：创建基础表结构
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
  `max_user_replies` int(11) NOT NULL DEFAULT 3 COMMENT '用户回复总次数限制，超过此次数就结束场景',
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
  KEY `idx_auto_switch_to_free` (`auto_switch_to_free`),
  KEY `idx_max_user_replies` (`max_user_replies`)
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
  `ai_message` text DEFAULT NULL COMMENT 'AI说的话（已废弃，保留用于兼容性）',
  `use_message_list` tinyint(1) DEFAULT 0 COMMENT '是否使用消息列表：0-使用单个消息 1-使用消息列表',
  `message_list_config` text COMMENT '消息列表配置，JSON格式',
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
  `alternative_message` text DEFAULT NULL COMMENT '替代消息（已废弃，保留用于兼容性）',
  `correct_response` text COMMENT '正确答案，用于教学模式判断',
  `praise_message` text DEFAULT NULL COMMENT '夸奖消息（已废弃，保留用于兼容性）',
  `encouragement_message` text DEFAULT NULL COMMENT '鼓励消息（已废弃，保留用于兼容性）',
  `auto_reply_on_timeout` text COMMENT '超时时的自动回复内容',
  `wait_time_seconds` int(11) DEFAULT 10 COMMENT '等待用户回复的时间（秒）',
  `gesture_hint` varchar(50) DEFAULT NULL COMMENT '手势提示：point_mouth/point_stomach等',
  `music_effect` varchar(100) DEFAULT NULL COMMENT '音效文件名',
  `encouragement_words` text COMMENT '鼓励词，步骤结束后播放的鼓励内容',
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

-- AI消息列表表
CREATE TABLE `ai_step_message` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `message_id` varchar(64) NOT NULL COMMENT '消息唯一标识',
  `step_id` varchar(64) NOT NULL COMMENT '关联的步骤ID',
  `scenario_id` varchar(64) NOT NULL COMMENT '关联的场景ID',
  `message_content` text NOT NULL COMMENT 'AI消息内容',
  `message_order` int(11) NOT NULL DEFAULT 1 COMMENT '消息顺序',
  `speech_rate` decimal(3,1) DEFAULT 1.0 COMMENT '语速配置：0.5-2.0倍速，1.0为正常语速',
  `wait_time_seconds` int(11) DEFAULT 3 COMMENT '等待时间（秒）',
  `parameters` text COMMENT '消息参数，JSON格式，如：{"emotion": "happy", "tone": "gentle"}',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用：0-禁用 1-启用',
  `message_type` varchar(32) DEFAULT 'normal' COMMENT '消息类型：normal/instruction/encouragement/feedback',
  `creator` bigint(20) DEFAULT NULL COMMENT '创建者ID',
  `create_date` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` bigint(20) DEFAULT NULL COMMENT '更新者ID',
  `update_date` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_message_id` (`message_id`),
  KEY `idx_step_id` (`step_id`),
  KEY `idx_scenario_id` (`scenario_id`),
  KEY `idx_message_order` (`message_order`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_message_type` (`message_type`),
  KEY `idx_step_message_order` (`step_id`, `message_order`),
  KEY `idx_step_scenario_order` (`step_id`, `scenario_id`, `message_order`),
  KEY `idx_active_messages` (`step_id`, `is_active`, `message_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='步骤AI消息列表表';

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
  `ai_message` text DEFAULT NULL COMMENT 'AI说的话模板（已废弃，保留用于兼容性）',
  `use_message_list` tinyint(1) DEFAULT 0 COMMENT '是否使用消息列表：0-使用单个消息 1-使用消息列表',
  `message_list_config` text COMMENT '消息列表配置，JSON格式',
  `expected_keywords` text COMMENT '期望的关键词模板',
  `expected_phrases` text COMMENT '期望的完整短语模板',
  `alternative_message` text DEFAULT NULL COMMENT '替代提示模板（已废弃，保留用于兼容性）',
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

-- 用户信息表
CREATE TABLE `user_info` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `device_id` varchar(50) NOT NULL COMMENT '设备ID，与设备绑定',
    `user_name` varchar(100) COMMENT '用户姓名',
    `user_nickname` varchar(100) COMMENT '用户昵称',
    `user_age` int(11) COMMENT '用户年龄',
    `user_gender` tinyint(1) COMMENT '用户性别：0-未知，1-男，2-女',
    `user_avatar` varchar(500) COMMENT '用户头像URL',
    `user_preferences` text COMMENT '用户偏好设置，JSON格式',
    `knowledge_base` text COMMENT '用户知识库，JSON格式存储用户相关信息',
    `first_interaction_time` datetime COMMENT '首次交互时间',
    `last_interaction_time` datetime COMMENT '最后交互时间',
    `interaction_count` int(11) DEFAULT 0 COMMENT '交互次数',
    `is_active` tinyint(1) DEFAULT 1 COMMENT '是否活跃：0-不活跃，1-活跃',
    `created_at` datetime(3) DEFAULT CURRENT_TIMESTAMP(3) NOT NULL COMMENT '创建时间',
    `updated_at` datetime(3) DEFAULT CURRENT_TIMESTAMP(3) NOT NULL ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_info_device_id` (`device_id`),
    KEY `idx_user_info_name` (`user_name`),
    KEY `idx_user_info_active` (`is_active`),
    KEY `idx_user_info_last_interaction` (`last_interaction_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户信息表';

-- 用户交互记录表
CREATE TABLE `user_interaction_log` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `device_id` varchar(50) NOT NULL COMMENT '设备ID',
    `user_name` varchar(100) COMMENT '用户姓名',
    `interaction_type` varchar(50) COMMENT '交互类型：greeting, question, command, etc.',
    `user_input` text COMMENT '用户输入内容',
    `ai_response` text COMMENT 'AI回复内容',
    `interaction_duration` int(11) COMMENT '交互持续时间（秒）',
    `created_at` datetime(3) DEFAULT CURRENT_TIMESTAMP(3) NOT NULL COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_interaction_device_id` (`device_id`),
    KEY `idx_user_interaction_type` (`interaction_type`),
    KEY `idx_user_interaction_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户交互记录表';

-- =====================================================
-- 第三部分：插入默认数据
-- =====================================================

-- 插入默认步骤模板
INSERT INTO `ai_step_template` (`template_id`, `template_code`, `template_name`, `template_type`, `ai_message`, `expected_keywords`, `expected_phrases`, `alternative_message`, `speech_rate`, `description`, `is_default`, `sort_order`) VALUES
('TEMPLATE_20241201000001', 'greeting_001', '问候模板', 'greeting', '你好！很高兴见到你！', '["你好", "早上好", "下午好"]', '["你好", "早上好", "下午好"]', '没关系，我们可以重新开始。', 1.0, '基础问候模板', 1, 1),
('TEMPLATE_20241201000002', 'instruction_001', '指令模板', 'instruction', '请按照我的指示来做。', '["好的", "明白了", "知道了"]', '["好的", "明白了", "知道了"]', '没关系，我再解释一遍。', 0.8, '基础指令模板（稍慢语速）', 1, 2),
('TEMPLATE_20241201000003', 'encouragement_001', '鼓励模板', 'encouragement', '做得很好！继续加油！', '["谢谢", "好的", "我会的"]', '["谢谢", "好的", "我会的"]', '没关系，下次会更好的。', 1.2, '基础鼓励模板（稍快语速）', 1, 3);

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
-- 第四部分：创建视图
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
-- 第五部分：数据修复和优化
-- =====================================================

-- 修复消息内容中的儿童姓名重复问题
UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '小朋友小朋友', '{childName}小朋友')
WHERE message_content LIKE '%小朋友小朋友%'
AND parameters LIKE '%"migrated": true%';

UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '文杰小朋友', '{childName}小朋友')
WHERE message_content LIKE '%文杰小朋友%'
AND parameters LIKE '%"migrated": true%';

UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '小明小朋友', '{childName}小朋友')
WHERE message_content LIKE '%小明小朋友%'
AND parameters LIKE '%"migrated": true%';

UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '小红小朋友', '{childName}小朋友')
WHERE message_content LIKE '%小红小朋友%'
AND parameters LIKE '%"migrated": true%';

UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '小华小朋友', '{childName}小朋友')
WHERE message_content LIKE '%小华小朋友%'
AND parameters LIKE '%"migrated": true%';

-- 将{文杰}统一替换为{childName}
UPDATE ai_step_message 
SET message_content = REPLACE(message_content, '{文杰}', '{childName}')
WHERE message_content LIKE '%{文杰}%'
AND parameters LIKE '%"migrated": true%';

-- 更新修复标记
UPDATE ai_step_message 
SET parameters = JSON_SET(parameters, '$.content_fixed', true, '$.fix_date', NOW())
WHERE parameters LIKE '%"migrated": true%'
AND parameters NOT LIKE '%"content_fixed": true%';

-- 清理现有数据中的空值
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

UPDATE ai_step_template 
SET ai_message = NULL 
WHERE ai_message = '';

UPDATE ai_step_template 
SET alternative_message = NULL 
WHERE alternative_message = '';

-- =====================================================
-- 第六部分：验证表结构完整性
-- =====================================================

-- 验证所有表的结构完整性
SELECT 
    'ai_scenario' as table_name,
    COUNT(*) as total_records,
    COUNT(is_default_teaching) as records_with_teaching_config,
    COUNT(teaching_mode_config) as records_with_mode_config,
    COUNT(max_user_replies) as records_with_max_replies
FROM ai_scenario
UNION ALL
SELECT 
    'ai_scenario_step' as table_name,
    COUNT(*) as total_records,
    COUNT(correct_response) as records_with_correct_response,
    COUNT(speech_rate) as records_with_speech_rate,
    COUNT(use_message_list) as records_with_message_list
FROM ai_scenario_step
UNION ALL
SELECT 
    'ai_step_template' as table_name,
    COUNT(*) as total_records,
    COUNT(template_id) as records_with_template_id,
    COUNT(speech_rate) as records_with_speech_rate,
    COUNT(use_message_list) as records_with_message_list
FROM ai_step_template
UNION ALL
SELECT 
    'ai_child_learning_record' as table_name,
    COUNT(*) as total_records,
    COUNT(update_date) as records_with_update_date,
    0 as records_with_mode_config,
    0 as records_with_max_replies
FROM ai_child_learning_record
UNION ALL
SELECT 
    'ai_step_message' as table_name,
    COUNT(*) as total_records,
    COUNT(message_content) as records_with_content,
    COUNT(speech_rate) as records_with_speech_rate,
    COUNT(is_active) as records_with_active_status
FROM ai_step_message
UNION ALL
SELECT 
    'user_info' as table_name,
    COUNT(*) as total_records,
    COUNT(device_id) as records_with_device_id,
    COUNT(user_name) as records_with_user_name,
    COUNT(is_active) as records_with_active_status
FROM user_info;

-- =====================================================
-- 脚本执行完成
-- =====================================================
-- 此脚本包含了2.0.0版本的所有数据库更新：
-- 
-- 1. 场景配置表 (ai_scenario)：
--    - 支持教学模式配置
--    - 支持用户回复次数限制
--    - 支持夸奖和鼓励消息配置
-- 
-- 2. 对话步骤配置表 (ai_scenario_step)：
--    - 支持语速配置 (speech_rate)
--    - 支持三种成功条件分支 (exact/partial/none)
--    - 支持消息列表功能
--    - 支持教学模式相关字段
--    - 支持交互体验字段 (手势、音效等)
-- 
-- 3. AI消息列表表 (ai_step_message)：
--    - 支持每个步骤的多个AI消息
--    - 支持消息参数配置
--    - 支持消息类型分类
--    - 支持消息启用/禁用
-- 
-- 4. 步骤模板表 (ai_step_template)：
--    - 支持语速配置
--    - 支持消息列表功能
-- 
-- 5. 儿童学习记录表 (ai_child_learning_record)：
--    - 支持学习统计和分析
--    - 支持更新时间跟踪
-- 
-- 6. 用户信息表 (user_info)：
--    - 支持用户基本信息管理
--    - 支持用户偏好设置
--    - 支持知识库存储
-- 
-- 7. 用户交互记录表 (user_interaction_log)：
--    - 支持交互历史记录
--    - 支持交互类型分类
-- 
-- 8. 视图和索引：
--    - 创建了统计视图便于数据分析
--    - 创建了必要的索引提高查询性能
-- 
-- 9. 数据修复：
--    - 修复了消息内容中的重复问题
--    - 统一了占位符格式
--    - 清理了空值数据
-- 
-- 执行后，所有表结构将与Java实体类完全匹配
-- 建议在执行后重启Spring Boot应用程序以确保所有更改生效
