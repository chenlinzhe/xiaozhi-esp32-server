package xiaozhi.modules.user.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.common.entity.BaseEntity;

/**
 * 用户交互记录实体
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("user_interaction_log")
public class UserInteractionLogEntity extends BaseEntity {
    /**
     * 设备ID
     */
    private String deviceId;
    
    /**
     * 用户姓名
     */
    private String userName;
    
    /**
     * 交互类型：greeting, question, command, etc.
     */
    private String interactionType;
    
    /**
     * 用户输入内容
     */
    private String userInput;
    
    /**
     * AI回复内容
     */
    private String aiResponse;
    
    /**
     * 交互持续时间（秒）
     */
    private Integer interactionDuration;
}

