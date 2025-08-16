package xiaozhi.modules.scenario.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.common.entity.BaseEntity;
import xiaozhi.common.convert.BooleanToIntegerDeserializer;

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

    @Schema(description = "场景唯一标识")
    @TableField("scenario_id")
    private String scenarioId;

    @Schema(description = "关联的智能体ID")
    @TableField("agent_id")
    private String agentId;

    @Schema(description = "场景编码")
    @TableField("scenario_code")
    private String scenarioCode;

    @Schema(description = "场景名称")
    @TableField("scenario_name")
    private String scenarioName;

    @Schema(description = "场景类型：express_needs/greeting/emotion等")
    @TableField("scenario_type")
    private String scenarioType;

    @Schema(description = "触发方式：voice/visual/button")
    @TableField("trigger_type")
    private String triggerType;

    @Schema(description = "语音触发关键词，JSON格式")
    @TableField("trigger_keywords")
    private String triggerKeywords;

    @Schema(description = "视觉触发卡片，JSON格式")
    @TableField("trigger_cards")
    private String triggerCards;

    @Schema(description = "场景描述")
    @TableField("description")
    private String description;

    @Schema(description = "难度等级：1-5")
    @TableField("difficulty_level")
    private Integer difficultyLevel;

    @Schema(description = "目标年龄：3-6/7-12等")
    @TableField("target_age")
    private String targetAge;

    @Schema(description = "排序权重")
    @TableField("sort_order")
    private Integer sortOrder;

    @Schema(description = "是否启用：0-禁用 1-启用")
    @JsonProperty("isActive")
    @JsonDeserialize(using = BooleanToIntegerDeserializer.class)
    @TableField("is_active")
    private Integer isActive;

    @Schema(description = "是否为默认教学场景：0-否 1-是")
    @TableField("is_default_teaching")
    private Integer isDefaultTeaching;

    @Schema(description = "教学模式配置，JSON格式")
    @TableField("teaching_mode_config")
    private String teachingModeConfig;

    @Schema(description = "完成后是否自动切换到自由模式：0-否 1-是")
    @TableField("auto_switch_to_free")
    private Integer autoSwitchToFree;

    @Schema(description = "夸奖消息列表，JSON格式")
    @TableField("praise_messages")
    private String praiseMessages;

    @Schema(description = "鼓励消息列表，JSON格式")
    @TableField("encouragement_messages")
    private String encouragementMessages;

    // 继承自BaseEntity的字段：id, creator, createDate
    // 需要单独定义的字段：
    @Schema(description = "更新者ID")
    @TableField("updater")
    private Long updater;

    @Schema(description = "更新时间")
    @TableField("update_date")
    private Date updateDate;

    // 扩展字段，用于前端显示
    @Schema(description = "步骤数量")
    @TableField(exist = false)
    private Integer stepCount;

    @Schema(description = "智能体名称")
    @TableField(exist = false)
    private String agentName;
} 