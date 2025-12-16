package xiaozhi.modules.device.service;

import xiaozhi.common.service.BaseService;
import xiaozhi.modules.device.dto.SendMessageDTO;
import xiaozhi.modules.device.entity.DeviceMessageEntity;

import java.util.List;

/**
 * 设备消息
 */
public interface DeviceMessageService extends BaseService<DeviceMessageEntity> {
    /**
     * 发送消息
     */
    void sendMessage(SendMessageDTO dto, Long userId);

    /**
     * 获取与指定设备的消息记录
     */
    List<DeviceMessageEntity> getMessageHistory(String deviceId, String friendDeviceId, Long userId);

    /**
     * 标记消息为已读
     */
    void markAsRead(String deviceId, String friendDeviceId, Long userId);
}
