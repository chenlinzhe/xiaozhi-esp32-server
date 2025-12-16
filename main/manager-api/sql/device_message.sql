-- 设备消息表
CREATE TABLE `device_message` (
  `id` bigint(20) NOT NULL COMMENT 'id',
  `from_device_id` varchar(100) NOT NULL COMMENT '发送方设备ID',
  `to_device_id` varchar(100) NOT NULL COMMENT '接收方设备ID',
  `content` text COMMENT '消息内容',
  `type` int(11) DEFAULT '0' COMMENT '消息类型 0:文本 1:图片 2:语音',
  `status` int(11) DEFAULT '0' COMMENT '状态 0:未读 1:已读',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_from_device` (`from_device_id`),
  KEY `idx_to_device` (`to_device_id`),
  KEY `idx_create_date` (`create_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备消息';
