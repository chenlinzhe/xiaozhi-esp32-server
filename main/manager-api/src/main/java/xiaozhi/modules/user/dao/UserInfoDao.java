package xiaozhi.modules.user.dao;

import org.apache.ibatis.annotations.Mapper;
import xiaozhi.common.dao.BaseDao;
import xiaozhi.modules.user.entity.UserInfoEntity;

/**
 * 用户信息Dao
 */
@Mapper
public interface UserInfoDao extends BaseDao<UserInfoEntity> {
    
}

