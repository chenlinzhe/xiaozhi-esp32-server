package xiaozhi.modules.device.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.util.Date;

/**
 * 设备消息
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_message")
public class DeviceMessageEntity {
    /**
     * id
     */
    private Long id;
    /**
     * 发送方设备ID
     */
    private String fromDeviceId;
    /**
     * 接收方设备ID
     */
    private String toDeviceId;
    /**
     * 消息内容
     */
    private String content;
    /**
     * 消息类型 0:文本 1:图片 2:语音
     */
    private Integer type;
    /**
     * 状态 0:未读 1:已读
     */
    private Integer status;
    /**
     * 创建时间
     */
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;
}
