package xiaozhi.modules.device.dao;

import org.apache.ibatis.annotations.Mapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import xiaozhi.modules.device.entity.DeviceMessageEntity;

/**
 * 设备消息
 */
@Mapper
public interface DeviceMessageDao extends BaseMapper<DeviceMessageEntity> {
}
