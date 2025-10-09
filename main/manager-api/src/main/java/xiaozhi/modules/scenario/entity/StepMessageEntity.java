package xiaozhi.modules.scenario.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.common.entity.BaseEntity;

import java.math.BigDecimal;
import java.util.Date;

/**
 * 步骤AI消息实体类
 * 
 * @author xiaozhi
 * @since 2025-01-01
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("ai_step_message")
@Schema(description = "步骤AI消息信息")
public class StepMessageEntity extends BaseEntity {

    @Schema(description = "消息唯一标识")
    @TableField("message_id")
    private String messageId;

    @Schema(description = "关联的步骤ID")
    @TableField("step_id")
    private String stepId;

    @Schema(description = "关联的场景ID")
    @TableField("scenario_id")
    private String scenarioId;

    @Schema(description = "AI消息内容")
    @TableField("message_content")
    private String messageContent;

    @Schema(description = "消息顺序")
    @TableField("message_order")
    private Integer messageOrder;

    @Schema(description = "语速配置：0.5-2.0倍速，1.0为正常语速")
    @TableField("speech_rate")
    private BigDecimal speechRate;

    @Schema(description = "等待时间（秒）")
    @TableField("wait_time_seconds")
    private Integer waitTimeSeconds;

    @Schema(description = "消息参数，JSON格式")
    @TableField("parameters")
    private String parameters;

    @Schema(description = "是否启用：0-禁用 1-启用")
    @TableField("is_active")
    private Integer isActive;

    @Schema(description = "消息类型：normal/instruction/encouragement/feedback")
    @TableField("message_type")
    private String messageType;

    @Schema(description = "创建者ID")
    @TableField("creator")
    private Long creator;

    @Schema(description = "创建时间")
    @TableField("create_date")
    private Date createDate;

    @Schema(description = "更新者ID")
    @TableField("updater")
    private Long updater;

    @Schema(description = "更新时间")
    @TableField("update_date")
    private Date updateDate;

    // 扩展字段，用于前端显示
    @Schema(description = "步骤名称")
    @TableField(exist = false)
    private String stepName;

    @Schema(description = "场景名称")
    @TableField(exist = false)
    private String scenarioName;
}
