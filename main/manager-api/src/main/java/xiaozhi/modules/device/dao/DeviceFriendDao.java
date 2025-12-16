package xiaozhi.modules.device.dao;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import xiaozhi.modules.device.entity.DeviceFriendEntity;

@Mapper
public interface DeviceFriendDao extends BaseMapper<DeviceFriendEntity> {
    // MyBatis Plus 提供基本的CRUD操作
    // 复杂查询可以在这里添加自定义方法
}
