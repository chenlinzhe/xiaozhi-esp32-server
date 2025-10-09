package xiaozhi.modules.user.controller;

import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import xiaozhi.common.utils.Result;
import xiaozhi.modules.user.entity.UserInfoEntity;
import xiaozhi.modules.user.service.UserInfoService;

/**
 * 用户信息Controller
 */
@RestController
@RequestMapping("/user")
public class UserInfoController {
    
    @Autowired
    private UserInfoService userInfoService;
    
    /**
     * 根据设备ID获取用户信息
     */
    @GetMapping("/device-info")
    public Result<UserInfoEntity> getUserInfo(@RequestParam String deviceId) {
        UserInfoEntity userInfo = userInfoService.getByDeviceId(deviceId);
        return new Result<UserInfoEntity>().ok(userInfo);
    }
    
    /**
     * 检查用户是否已设置姓名
     */
    @GetMapping("/has-name")
    public Result<Boolean> hasUserName(@RequestParam String deviceId) {
        boolean hasName = userInfoService.hasUserName(deviceId);
        return new Result<Boolean>().ok(hasName);
    }
    
    /**
     * 更新用户姓名
     */
    @PostMapping("/update-name")
    public Result<Boolean> updateUserName(@RequestBody Map<String, String> request) {
        String deviceId = request.get("deviceId");
        String userName = request.get("userName");
        
        if (deviceId == null || userName == null) {
            return new Result<Boolean>().error("设备ID和用户名不能为空");
        }
        
        boolean success = userInfoService.updateUserName(deviceId, userName);
        return new Result<Boolean>().ok(success);
    }
    
    /**
     * 更新用户知识库
     */
    @PostMapping("/update-knowledge")
    public Result<Boolean> updateKnowledgeBase(@RequestBody Map<String, String> request) {
        String deviceId = request.get("deviceId");
        String knowledgeBase = request.get("knowledgeBase");
        
        if (deviceId == null) {
            return new Result<Boolean>().error("设备ID不能为空");
        }
        
        boolean success = userInfoService.updateKnowledgeBase(deviceId, knowledgeBase);
        return new Result<Boolean>().ok(success);
    }
    
    /**
     * 获取用户知识库
     */
    @GetMapping("/knowledge")
    public Result<String> getKnowledgeBase(@RequestParam String deviceId) {
        String knowledgeBase = userInfoService.getKnowledgeBase(deviceId);
        return new Result<String>().ok(knowledgeBase);
    }
    
    /**
     * 记录用户交互
     */
    @PostMapping("/interaction")
    public Result<Boolean> recordInteraction(@RequestBody Map<String, String> request) {
        String deviceId = request.get("deviceId");
        String interactionType = request.get("interactionType");
        String userInput = request.get("userInput");
        String aiResponse = request.get("aiResponse");
        
        if (deviceId == null) {
            return new Result<Boolean>().error("设备ID不能为空");
        }
        
        userInfoService.recordInteraction(deviceId, interactionType, userInput, aiResponse);
        return new Result<Boolean>().ok(true);
    }
}

