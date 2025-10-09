package xiaozhi.modules.user.service;

import xiaozhi.common.service.BaseService;
import xiaozhi.modules.user.entity.UserInfoEntity;

/**
 * 用户信息Service
 */
public interface UserInfoService extends BaseService<UserInfoEntity> {
    
    /**
     * 根据设备ID获取用户信息
     */
    UserInfoEntity getByDeviceId(String deviceId);
    
    /**
     * 创建或更新用户信息
     */
    UserInfoEntity createOrUpdateUser(UserInfoEntity userInfo);
    
    /**
     * 更新用户姓名
     */
    boolean updateUserName(String deviceId, String userName);
    
    /**
     * 更新用户知识库
     */
    boolean updateKnowledgeBase(String deviceId, String knowledgeBase);
    
    /**
     * 记录用户交互
     */
    void recordInteraction(String deviceId, String interactionType, String userInput, String aiResponse);
    
    /**
     * 检查用户是否已设置姓名
     */
    boolean hasUserName(String deviceId);
    
    /**
     * 获取用户知识库
     */
    String getKnowledgeBase(String deviceId);
}

