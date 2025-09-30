-- 创建用户信息表
DROP TABLE IF EXISTS user_info;

CREATE TABLE user_info (
    id BIGINT AUTO_INCREMENT COMMENT '主键ID' PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL COMMENT '设备ID，与设备绑定',
    user_name VARCHAR(100) COMMENT '用户姓名',
    user_nickname VARCHAR(100) COMMENT '用户昵称',
    user_age INT COMMENT '用户年龄',
    user_gender TINYINT COMMENT '用户性别：0-未知，1-男，2-女',
    user_avatar VARCHAR(500) COMMENT '用户头像URL',
    user_preferences TEXT COMMENT '用户偏好设置，JSON格式',
    knowledge_base TEXT COMMENT '用户知识库，JSON格式存储用户相关信息',
    first_interaction_time DATETIME COMMENT '首次交互时间',
    last_interaction_time DATETIME COMMENT '最后交互时间',
    interaction_count INT DEFAULT 0 COMMENT '交互次数',
    is_active TINYINT DEFAULT 1 COMMENT '是否活跃：0-不活跃，1-活跃',
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) NOT NULL COMMENT '创建时间',
    updated_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) NOT NULL ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
    
    -- 索引
    UNIQUE KEY uk_user_info_device_id (device_id),
    INDEX idx_user_info_name (user_name),
    INDEX idx_user_info_active (is_active),
    INDEX idx_user_info_last_interaction (last_interaction_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

-- 创建用户交互记录表
DROP TABLE IF EXISTS user_interaction_log;

CREATE TABLE user_interaction_log (
    id BIGINT AUTO_INCREMENT COMMENT '主键ID' PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL COMMENT '设备ID',
    user_name VARCHAR(100) COMMENT '用户姓名',
    interaction_type VARCHAR(50) COMMENT '交互类型：greeting, question, command, etc.',
    user_input TEXT COMMENT '用户输入内容',
    ai_response TEXT COMMENT 'AI回复内容',
    interaction_duration INT COMMENT '交互持续时间（秒）',
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) NOT NULL COMMENT '创建时间',
    
    -- 索引
    INDEX idx_user_interaction_device_id (device_id),
    INDEX idx_user_interaction_type (interaction_type),
    INDEX idx_user_interaction_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户交互记录表';

