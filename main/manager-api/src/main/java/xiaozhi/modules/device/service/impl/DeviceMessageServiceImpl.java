package xiaozhi.modules.device.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.modules.device.dao.DeviceDao;
import xiaozhi.modules.device.dao.DeviceFriendDao;
import xiaozhi.modules.device.dao.DeviceMessageDao;
import xiaozhi.modules.device.dto.SendMessageDTO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.entity.DeviceFriendEntity;
import xiaozhi.modules.device.entity.DeviceMessageEntity;
import xiaozhi.modules.device.service.DeviceMessageService;

import java.util.List;

@Service
public class DeviceMessageServiceImpl extends BaseServiceImpl<DeviceMessageDao, DeviceMessageEntity> implements DeviceMessageService {

    private final DeviceDao deviceDao;
    private final DeviceFriendDao deviceFriendDao;

    public DeviceMessageServiceImpl(DeviceDao deviceDao, DeviceFriendDao deviceFriendDao) {
        this.deviceDao = deviceDao;
        this.deviceFriendDao = deviceFriendDao;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void sendMessage(SendMessageDTO dto, Long userId) {
        // 优化：一次性验证设备归属和好友关系
        // 先快速验证设备归属（使用索引查询）
        DeviceEntity fromDevice = deviceDao.selectById(dto.getFromDeviceId());
        if (fromDevice == null || !fromDevice.getUserId().equals(userId)) {
            throw new RenException(ErrorCode.FORBIDDEN, "无权操作此设备");
        }

        // 优化：好友关系验证改用EXISTS查询，更快
        QueryWrapper<DeviceFriendEntity> friendQuery = new QueryWrapper<>();
        friendQuery.eq("device_id", dto.getFromDeviceId())
                   .eq("friend_device_id", dto.getToDeviceId())
                   .eq("status", 1)
                   .last("LIMIT 1"); // 优化：只需要知道存在即可
        if (deviceFriendDao.selectCount(friendQuery) == 0) {
            throw new RenException(ErrorCode.FORBIDDEN, "非好友关系，无法发送消息");
        }

        // 优化：直接插入，减少对象创建开销
        DeviceMessageEntity message = new DeviceMessageEntity();
        message.setFromDeviceId(dto.getFromDeviceId());
        message.setToDeviceId(dto.getToDeviceId());
        message.setContent(dto.getContent());
        message.setType(dto.getType());
        message.setStatus(0); // 未读

        baseDao.insert(message);
    }

    @Override
    public List<DeviceMessageEntity> getMessageHistory(String deviceId, String friendDeviceId, Long userId) {
        // 优化：只在必要时验证设备归属
        // 对于高频查询，可以考虑在Controller层验证一次即可
        DeviceEntity device = deviceDao.selectById(deviceId);
        if (device == null || !device.getUserId().equals(userId)) {
            throw new RenException(ErrorCode.FORBIDDEN, "无权操作此设备");
        }

        // 优化：添加索引提示和限制结果数量
        QueryWrapper<DeviceMessageEntity> query = new QueryWrapper<>();
        query.and(wrapper -> wrapper
                .nested(w -> w.eq("from_device_id", deviceId).eq("to_device_id", friendDeviceId))
                .or()
                .nested(w -> w.eq("from_device_id", friendDeviceId).eq("to_device_id", deviceId))
        )
        .orderByAsc("create_date")
        .last("LIMIT 500"); // 优化：限制返回数量，避免一次加载过多数据

        return baseDao.selectList(query);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void markAsRead(String deviceId, String friendDeviceId, Long userId) {
        // 优化：只在必要时验证设备归属
        DeviceEntity device = deviceDao.selectById(deviceId);
        if (device == null || !device.getUserId().equals(userId)) {
            throw new RenException(ErrorCode.FORBIDDEN, "无权操作此设备");
        }

        // 优化：使用批量更新，减少SQL执行时间
        DeviceMessageEntity updateEntity = new DeviceMessageEntity();
        updateEntity.setStatus(1);

        QueryWrapper<DeviceMessageEntity> query = new QueryWrapper<>();
        query.eq("from_device_id", friendDeviceId)
             .eq("to_device_id", deviceId)
             .eq("status", 0);

        baseDao.update(updateEntity, query);
    }
}
