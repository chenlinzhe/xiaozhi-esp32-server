-- 添加用户回复总次数字段到场景配置表
-- 执行时间：2025-01-03
-- 功能：为场景配置添加用户回复总次数限制，超过3次就结束场景

-- 添加用户回复总次数字段
ALTER TABLE `ai_scenario` 
ADD COLUMN `max_user_replies` int(11) DEFAULT 3 COMMENT '用户回复总次数限制，超过此次数就结束场景' 
AFTER `auto_switch_to_free`;

-- 添加索引以提高查询性能
ALTER TABLE `ai_scenario` 
ADD INDEX `idx_max_user_replies` (`max_user_replies`);

-- 更新现有数据，设置默认值为3
UPDATE `ai_scenario` SET `max_user_replies` = 3 WHERE `max_user_replies` IS NULL;

-- 添加注释说明
ALTER TABLE `ai_scenario` 
MODIFY COLUMN `max_user_replies` int(11) NOT NULL DEFAULT 3 COMMENT '用户回复总次数限制，超过此次数就结束场景';

-- 脚本执行完成
-- 新增功能：
-- 1. 用户回复总次数限制字段 (max_user_replies)：支持配置场景中用户回复的总次数限制
-- 2. 默认值为3次，超过3次回复就自动结束场景
-- 3. 添加索引以提高查询性能
-- 
-- 执行后，场景配置表将支持用户回复总次数限制功能
-- 建议在执行后重启应用程序以确保所有更改生效
