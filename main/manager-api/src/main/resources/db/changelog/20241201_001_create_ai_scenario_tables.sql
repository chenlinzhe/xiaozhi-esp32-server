-- =====================================================
-- 场景配置相关表结构
-- 创建时间：2024-12-01
-- 描述：AI场景配置、步骤配置、学习记录和模板管理
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
  KEY `idx_agent_type_active` (`agent_id`, `scenario_type`, `is_active`)
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
  `success_condition` varchar(20) DEFAULT 'exact' COMMENT '成功条件：exact/partial/keyword',
  `next_step_id` varchar(64) DEFAULT NULL COMMENT '成功后的下一步ID',
  `retry_step_id` varchar(64) DEFAULT NULL COMMENT '失败后的重试步骤ID',
  `alternative_message` text COMMENT '失败时的替代提示',
  `gesture_hint` varchar(50) DEFAULT NULL COMMENT '手势提示：point_mouth/point_stomach等',
  `music_effect` varchar(100) DEFAULT NULL COMMENT '音效文件名',
  `is_optional` tinyint(1) DEFAULT 0 COMMENT '是否可选步骤：0-必需 1-可选',
  `branch_condition` text COMMENT '分支条件，JSON格式',
  `create_date` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` bigint(20) DEFAULT NULL COMMENT '更新者ID',
  `update_date` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_step_id` (`step_id`),
  UNIQUE KEY `uk_scenario_step` (`scenario_id`, `step_code`),
  KEY `idx_scenario_id` (`scenario_id`),
  KEY `idx_step_order` (`step_order`),
  KEY `idx_step_type` (`step_type`),
  KEY `idx_next_step_id` (`next_step_id`),
  KEY `idx_retry_step_id` (`retry_step_id`),
  KEY `idx_scenario_order` (`scenario_id`, `step_order`)
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
  `template_code` varchar(64) NOT NULL COMMENT '模板编码',
  `template_name` varchar(128) NOT NULL COMMENT '模板名称',
  `template_type` varchar(32) NOT NULL COMMENT '模板类型：greeting/instruction/encouragement等',
  `ai_message` text NOT NULL COMMENT 'AI说的话模板',
  `expected_keywords` text COMMENT '期望的关键词模板',
  `expected_phrases` text COMMENT '期望的完整短语模板',
  `alternative_message` text COMMENT '替代提示模板',
  `description` text COMMENT '模板描述',
  `is_default` tinyint(1) DEFAULT 0 COMMENT '是否默认模板',
  `sort_order` int(11) DEFAULT 0 COMMENT '排序权重',
  `creator` bigint(20) DEFAULT NULL COMMENT '创建者ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_template_code` (`template_code`),
  KEY `idx_template_type` (`template_type`),
  KEY `idx_is_default` (`is_default`),
  KEY `idx_sort_order` (`sort_order`),
  KEY `idx_type_default` (`template_type`, `is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='步骤模板表';

-- =====================================================
-- 插入默认数据
-- =====================================================

-- 插入默认步骤模板
INSERT INTO `ai_step_template` (`template_code`, `template_name`, `template_type`, `ai_message`, `expected_keywords`, `expected_phrases`, `alternative_message`, `description`, `is_default`, `sort_order`) VALUES
('greeting_001', '问候模板', 'greeting', '你好！很高兴见到你！', '["你好", "早上好", "下午好"]', '["你好", "早上好", "下午好"]', '没关系，我们可以重新开始。', '基础问候模板', 1, 1),
('instruction_001', '指令模板', 'instruction', '请按照我的指示来做。', '["好的", "明白了", "知道了"]', '["好的", "明白了", "知道了"]', '没关系，我再解释一遍。', '基础指令模板', 1, 2),
('encouragement_001', '鼓励模板', 'encouragement', '做得很好！继续加油！', '["谢谢", "好的", "我会的"]', '["谢谢", "好的", "我会的"]', '没关系，下次会更好的。', '基础鼓励模板', 1, 3);

-- =====================================================
-- 创建视图（可选）
-- =====================================================

-- 场景统计视图
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

-- 儿童学习统计视图
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
