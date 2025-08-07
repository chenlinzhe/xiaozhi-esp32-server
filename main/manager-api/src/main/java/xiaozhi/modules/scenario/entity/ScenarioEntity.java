package xiaozhi.modules.scenario.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.common.entity.BaseEntity;

import java.util.Date;

/**
 * 场景配置实体类
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("ai_scenario")
@Schema(description = "场景配置信息")
public class ScenarioEntity extends BaseEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "场景唯一标识")
    private String id;

    @Schema(description = "关联的智能体ID")
    private String agentId;

    @Schema(description = "场景编码")
    private String scenarioCode;

    @Schema(description = "场景名称")
    private String scenarioName;

    @Schema(description = "场景类型：express_needs/greeting/emotion等")
    private String scenarioType;

    @Schema(description = "触发方式：voice/visual/button")
    private String triggerType;

    @Schema(description = "语音触发关键词，JSON格式")
    private String triggerKeywords;

    @Schema(description = "视觉触发卡片，JSON格式")
    private String triggerCards;

    @Schema(description = "场景描述")
    private String description;

    @Schema(description = "难度等级：1-5")
    private Integer difficultyLevel;

    @Schema(description = "目标年龄：3-6/7-12等")
    private String targetAge;

    @Schema(description = "排序权重")
    private Integer sortOrder;

    @Schema(description = "是否启用：0-禁用 1-启用")
    private Integer isActive;

    @Schema(description = "创建者ID")
    private Long creator;

    @Schema(description = "创建时间")
    private Date createdAt;

    @Schema(description = "更新者ID")
    private Long updater;

    @Schema(description = "更新时间")
    private Date updatedAt;

    // 扩展字段，用于前端显示
    @Schema(description = "步骤数量")
    private Integer stepCount;

    @Schema(description = "智能体名称")
    private String agentName;
} 