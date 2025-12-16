package xiaozhi.modules.device.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_friend")
@Schema(description = "设备好友关系")
public class DeviceFriendEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "ID")
    private String id;

    @Schema(description = "设备ID")
    private String deviceId;

    @Schema(description = "好友设备ID")
    private String friendDeviceId;

    @Schema(description = "好友设备MAC地址")
    private String friendMacAddress;

    @Schema(description = "好友用户名")
    private String friendUsername;

    @Schema(description = "好友智能体名称")
    private String friendAgentName;

    @Schema(description = "状态：0-待确认，1-已同意，2-已拒绝")
    private Integer status;

    @Schema(description = "创建者")
    @TableField(fill = FieldFill.INSERT)
    private String creator;  // 修复：改为String与数据库一致

    @Schema(description = "创建时间")
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;

    @Schema(description = "更新者")
    @TableField(fill = FieldFill.UPDATE)
    private String updater;  // 修复：改为String与数据库一致

    @Schema(description = "更新时间")
    @TableField(fill = FieldFill.UPDATE)
    private Date updateDate;
}
