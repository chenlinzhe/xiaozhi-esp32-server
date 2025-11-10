package xiaozhi.modules.user.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 用户信息实体
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("user_info")
public class UserInfoEntity {
    /**
     * 主键ID
     */
    private Long id;
    /**
     * 设备ID
     */
    private String deviceId;
    
    /**
     * 用户姓名
     */
    private String userName;
    
    /**
     * 用户昵称
     */
    private String userNickname;
    
    /**
     * 用户年龄
     */
    private Integer userAge;
    
    /**
     * 用户性别：0-未知，1-男，2-女
     */
    private Integer userGender;
    
    /**
     * 用户头像URL
     */
    private String userAvatar;
    
    /**
     * 用户偏好设置，JSON格式
     */
    private String userPreferences;
    
    /**
     * 用户知识库，JSON格式存储用户相关信息
     */
    private String knowledgeBase;
    
    /**
     * 首次交互时间
     */
    private Date firstInteractionTime;
    
    /**
     * 最后交互时间
     */
    private Date lastInteractionTime;
    
    /**
     * 交互次数
     */
    private Integer interactionCount;
    
    /**
     * 是否活跃：0-不活跃，1-活跃
     */
    private Integer isActive;

    /**
     * 创建时间
     */
    @TableField(fill = FieldFill.INSERT)
    private Date createdAt;

    /**
     * 更新时间
     */
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private Date updatedAt;
}

