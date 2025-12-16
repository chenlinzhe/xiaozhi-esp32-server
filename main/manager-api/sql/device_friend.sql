-- 设备好友关系表
CREATE TABLE IF NOT EXISTS `device_friend` (
    `id` VARCHAR(32) NOT NULL COMMENT '主键ID',
    `device_id` VARCHAR(32) NOT NULL COMMENT '设备ID',
    `friend_device_id` VARCHAR(32) NOT NULL COMMENT '好友设备ID',
    `friend_mac_address` VARCHAR(50) DEFAULT NULL COMMENT '好友设备MAC地址',
    `friend_username` VARCHAR(100) DEFAULT NULL COMMENT '好友用户名',
    `friend_agent_name` VARCHAR(100) DEFAULT NULL COMMENT '好友智能体名称',
    `status` TINYINT DEFAULT 0 COMMENT '状态：0-待确认，1-已同意，2-已拒绝',
    `creator` VARCHAR(32) DEFAULT NULL COMMENT '创建者',
    `create_date` DATETIME DEFAULT NULL COMMENT '创建时间',
    `updater` VARCHAR(32) DEFAULT NULL COMMENT '更新者',
    `update_date` DATETIME DEFAULT NULL COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_device_id` (`device_id`),
    KEY `idx_friend_device_id` (`friend_device_id`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备好友关系表';

-- 创建索引优化查询
CREATE INDEX idx_device_status ON device_friend(device_id, status);
CREATE INDEX idx_friend_status ON device_friend(friend_device_id, status);
