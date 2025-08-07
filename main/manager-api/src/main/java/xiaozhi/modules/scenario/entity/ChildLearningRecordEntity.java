package xiaozhi.modules.scenario.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.common.entity.BaseEntity;

import java.math.BigDecimal;
import java.util.Date;

/**
 * 儿童学习记录实体类
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("ai_child_learning_record")
@Schema(description = "儿童学习记录信息")
public class ChildLearningRecordEntity extends BaseEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "记录唯一标识")
    private String id;

    @Schema(description = "智能体ID")
    private String agentId;

    @Schema(description = "场景ID")
    private String scenarioId;

    @Schema(description = "儿童姓名")
    private String childName;

    @Schema(description = "开始时间")
    private Date startTime;

    @Schema(description = "结束时间")
    private Date endTime;

    @Schema(description = "总步骤数")
    private Integer totalSteps;

    @Schema(description = "完成步骤数")
    private Integer completedSteps;

    @Schema(description = "成功率百分比")
    private BigDecimal successRate;

    @Schema(description = "学习时长(秒)")
    private Integer learningDuration;

    @Schema(description = "难度评分：1-5")
    private Integer difficultyRating;

    @Schema(description = "学习笔记")
    private String notes;

    @Schema(description = "创建时间")
    private Date createdAt;

    // 扩展字段，用于前端显示
    @Schema(description = "场景名称")
    private String scenarioName;

    @Schema(description = "智能体名称")
    private String agentName;

    @Schema(description = "学习时长格式化")
    private String learningDurationFormatted;
} 