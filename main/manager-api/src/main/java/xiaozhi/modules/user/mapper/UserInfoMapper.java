package xiaozhi.modules.user.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import xiaozhi.common.dao.BaseDao;
import xiaozhi.modules.user.entity.UserInfoEntity;

/**
 * 用户信息Mapper
 */
@Mapper
public interface UserInfoMapper extends BaseDao<UserInfoEntity> {
    
    /**
     * 根据设备ID查询用户信息
     */
    UserInfoEntity getByDeviceId(@Param("deviceId") String deviceId);
    
    /**
     * 更新用户最后交互时间
     */
    int updateLastInteractionTime(@Param("deviceId") String deviceId);
    
    /**
     * 增加交互次数
     */
    int incrementInteractionCount(@Param("deviceId") String deviceId);
}

