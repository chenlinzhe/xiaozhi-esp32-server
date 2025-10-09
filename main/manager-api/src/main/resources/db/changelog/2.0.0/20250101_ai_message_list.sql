-- 数据库变更脚本 - AI消息列表支持
-- =====================================================
-- 创建时间：2025-01-01
-- 描述：为步骤配置添加AI消息列表支持，每个步骤可以有多个AI消息
-- 注意：保持与现有系统的完全兼容性
-- =====================================================

-- =====================================================
-- 第一部分：创建AI消息列表表
-- =====================================================

-- 创建AI消息列表表
CREATE TABLE IF NOT EXISTS `ai_step_message` (
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
  KEY `idx_step_message_order` (`step_id`, `message_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='步骤AI消息列表表';

-- =====================================================
-- 第二部分：修改现有步骤表，添加消息列表支持（向后兼容）
-- =====================================================

-- 为ai_scenario_step表添加消息列表相关字段
ALTER TABLE `ai_scenario_step` 
ADD COLUMN `use_message_list` tinyint(1) DEFAULT 0 COMMENT '是否使用消息列表：0-使用单个消息 1-使用消息列表' AFTER `ai_message`,
ADD COLUMN `message_list_config` text COMMENT '消息列表配置，JSON格式' AFTER `use_message_list`;

-- 为ai_step_template表添加消息列表相关字段
ALTER TABLE `ai_step_template` 
ADD COLUMN `use_message_list` tinyint(1) DEFAULT 0 COMMENT '是否使用消息列表：0-使用单个消息 1-使用消息列表' AFTER `ai_message`,
ADD COLUMN `message_list_config` text COMMENT '消息列表配置，JSON格式' AFTER `use_message_list`;

-- =====================================================
-- 第三部分：创建必要的索引
-- =====================================================

-- 为消息列表表添加复合索引
CREATE INDEX `idx_step_scenario_order` ON `ai_step_message` (`step_id`, `scenario_id`, `message_order`);
CREATE INDEX `idx_active_messages` ON `ai_step_message` (`step_id`, `is_active`, `message_order`);

-- =====================================================
-- 第四部分：数据迁移（保持现有数据完整性）
-- =====================================================

-- 将现有的ai_message数据迁移到消息列表表（保持向后兼容）
-- 这样现有的步骤仍然可以正常工作
INSERT INTO ai_step_message (message_id, step_id, scenario_id, message_content, message_order, speech_rate, wait_time_seconds, parameters, message_type, is_active)
SELECT 
  CONCAT('migrated_', step_id, '_', ROW_NUMBER() OVER (PARTITION BY step_id ORDER BY step_id)) as message_id,
  step_id,
  scenario_id,
  ai_message,
  1 as message_order,
  COALESCE(speech_rate, 1.0) as speech_rate,
  COALESCE(wait_time_seconds, 3) as wait_time_seconds,
  '{"migrated": true, "original_message": true}' as parameters,
  'normal' as message_type,
  1 as is_active
FROM ai_scenario_step 
WHERE ai_message IS NOT NULL AND ai_message != '';

-- =====================================================
-- 第五部分：验证表结构
-- =====================================================

-- 验证ai_step_message表结构
DESCRIBE ai_step_message;

-- 验证ai_scenario_step表新增字段
SELECT 
  COLUMN_NAME,
  DATA_TYPE,
  IS_NULLABLE,
  COLUMN_DEFAULT,
  COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ai_scenario_step' 
AND COLUMN_NAME IN ('use_message_list', 'message_list_config');

-- 验证ai_step_template表新增字段
SELECT 
  COLUMN_NAME,
  DATA_TYPE,
  IS_NULLABLE,
  COLUMN_DEFAULT,
  COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'ai_step_template' 
AND COLUMN_NAME IN ('use_message_list', 'message_list_config');

-- =====================================================
-- 第六部分：示例数据插入（可选）
-- =====================================================

-- 插入示例消息（可选）
/*
INSERT INTO ai_step_message (message_id, step_id, scenario_id, message_content, message_order, speech_rate, wait_time_seconds, parameters, message_type) VALUES
('msg_001', 'step_001', 'scenario_001', '你好，小朋友！', 1, 1.0, 2, '{"emotion": "friendly", "tone": "gentle"}', 'normal'),
('msg_002', 'step_001', 'scenario_001', '今天我们来学习一些有趣的东西', 2, 0.8, 3, '{"emotion": "excited", "tone": "enthusiastic"}', 'instruction'),
('msg_003', 'step_001', 'scenario_001', '准备好了吗？', 3, 1.2, 2, '{"emotion": "encouraging", "tone": "questioning"}', 'feedback');
*/

-- =====================================================
-- 脚本执行完成
-- =====================================================
-- 此脚本实现了以下功能：
-- 1. 创建了ai_step_message表，支持每个步骤的多个AI消息
-- 2. 每个消息包含：内容、语速、等待时间、参数等配置
-- 3. 修改了现有步骤表，添加了消息列表支持开关（向后兼容）
-- 4. 创建了必要的索引以提高查询性能
-- 5. 自动迁移现有数据，确保系统正常运行
-- 
-- 执行后，系统将支持：
-- - 每个步骤可以有多个AI消息
-- - 每个消息可以独立配置语速、等待时间、参数
-- - 消息可以按顺序播放
-- - 支持消息的启用/禁用
-- - 支持不同类型的消息（普通、指令、鼓励、反馈等）
-- - 完全向后兼容，现有功能不受影响
-- 
-- 建议在执行后重启Spring Boot应用程序以确保所有更改生效
