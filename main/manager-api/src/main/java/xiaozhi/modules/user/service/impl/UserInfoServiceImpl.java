package xiaozhi.modules.user.service.impl;

import java.util.Date;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.modules.user.dao.UserInfoDao;
import xiaozhi.modules.user.entity.UserInfoEntity;
import xiaozhi.modules.user.entity.UserInteractionLogEntity;
import xiaozhi.modules.user.mapper.UserInfoMapper;
import xiaozhi.modules.user.service.UserInfoService;

/**
 * 用户信息Service实现
 */
@Service
public class UserInfoServiceImpl extends BaseServiceImpl<UserInfoDao, UserInfoEntity> implements UserInfoService {
    
    @Autowired
    private UserInfoMapper userInfoMapper;
    
    @Override
    public UserInfoEntity getByDeviceId(String deviceId) {
        return userInfoMapper.getByDeviceId(deviceId);
    }
    
    @Override
    @Transactional
    public UserInfoEntity createOrUpdateUser(UserInfoEntity userInfo) {
        UserInfoEntity existingUser = getByDeviceId(userInfo.getDeviceId());
        
        if (existingUser == null) {
            // 创建新用户
            userInfo.setFirstInteractionTime(new Date());
            userInfo.setLastInteractionTime(new Date());
            userInfo.setInteractionCount(1);
            userInfo.setIsActive(1);
            insert(userInfo);
            return userInfo;
        } else {
            // 更新现有用户
            existingUser.setLastInteractionTime(new Date());
            userInfoMapper.incrementInteractionCount(userInfo.getDeviceId());
            updateById(existingUser);
            return existingUser;
        }
    }
    
    @Override
    @Transactional
    public boolean updateUserName(String deviceId, String userName) {
        UserInfoEntity user = getByDeviceId(deviceId);
        if (user == null) {
            // 创建新用户记录
            user = new UserInfoEntity();
            user.setDeviceId(deviceId);
            user.setUserName(userName);
            user.setFirstInteractionTime(new Date());
            user.setLastInteractionTime(new Date());
            user.setInteractionCount(1);
            user.setIsActive(1);
            insert(user);
        } else {
            // 更新现有用户
            user.setUserName(userName);
            user.setLastInteractionTime(new Date());
            userInfoMapper.incrementInteractionCount(deviceId);
            updateById(user);
        }
        return true;
    }
    
    @Override
    @Transactional
    public boolean updateKnowledgeBase(String deviceId, String knowledgeBase) {
        UserInfoEntity user = getByDeviceId(deviceId);
        if (user != null) {
            user.setKnowledgeBase(knowledgeBase);
            user.setLastInteractionTime(new Date());
            updateById(user);
            return true;
        }
        return false;
    }
    
    @Override
    @Transactional
    public void recordInteraction(String deviceId, String interactionType, String userInput, String aiResponse) {
        // 更新用户最后交互时间
        userInfoMapper.updateLastInteractionTime(deviceId);
        userInfoMapper.incrementInteractionCount(deviceId);
        
        // 记录交互日志
        UserInteractionLogEntity log = new UserInteractionLogEntity();
        log.setDeviceId(deviceId);
        log.setInteractionType(interactionType);
        log.setUserInput(userInput);
        log.setAiResponse(aiResponse);
        log.setCreateDate(new Date());
        
        // 这里可以添加交互日志的保存逻辑
        // interactionLogService.insert(log);
    }
    
    @Override
    public boolean hasUserName(String deviceId) {
        UserInfoEntity user = getByDeviceId(deviceId);
        return user != null && user.getUserName() != null && !user.getUserName().trim().isEmpty();
    }
    
    @Override
    public String getKnowledgeBase(String deviceId) {
        UserInfoEntity user = getByDeviceId(deviceId);
        return user != null ? user.getKnowledgeBase() : null;
    }
}

