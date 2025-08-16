package xiaozhi.modules.scenario.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.common.entity.BaseEntity;

import java.util.Date;

/**
 * 对话步骤配置实体类
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("ai_scenario_step")
@Schema(description = "对话步骤配置信息")
public class ScenarioStepEntity extends BaseEntity {

    @Schema(description = "步骤唯一标识")
    @TableField("step_id")
    private String stepId;

    @Schema(description = "关联的场景ID")
    @TableField("scenario_id")
    private String scenarioId;

    @Schema(description = "步骤编码")
    @TableField("step_code")
    private String stepCode;

    @Schema(description = "步骤名称")
    @TableField("step_name")
    private String stepName;

    @Schema(description = "步骤顺序")
    @TableField("step_order")
    private Integer stepOrder;

    @Schema(description = "AI说的话（固定配置的语句）")
    @TableField("ai_message")
    private String aiMessage;

    @Schema(description = "期望的关键词，JSON格式")
    @TableField("expected_keywords")
    private String expectedKeywords;

    @Schema(description = "期望的完整短语，JSON格式")
    @TableField("expected_phrases")
    private String expectedPhrases;

    @Schema(description = "最大尝试次数")
    @TableField("max_attempts")
    private Integer maxAttempts;

    @Schema(description = "等待超时时间(秒)")
    @TableField("timeout_seconds")
    private Integer timeoutSeconds;

    @Schema(description = "成功条件：exact/partial/keyword")
    @TableField("success_condition")
    private String successCondition;

    @Schema(description = "成功后的下一步ID")
    @TableField("next_step_id")
    private String nextStepId;

    @Schema(description = "失败后的重试步骤ID")
    @TableField("retry_step_id")
    private String retryStepId;

    @Schema(description = "失败时的替代提示")
    @TableField("alternative_message")
    private String alternativeMessage;

    @Schema(description = "正确答案，用于教学模式判断")
    @TableField("correct_response")
    private String correctResponse;

    @Schema(description = "回答正确时的夸奖消息")
    @TableField("praise_message")
    private String praiseMessage;

    @Schema(description = "回答错误时的鼓励消息")
    @TableField("encouragement_message")
    private String encouragementMessage;

    @Schema(description = "超时时的自动回复内容")
    @TableField("auto_reply_on_timeout")
    private String autoReplyOnTimeout;

    @Schema(description = "等待用户回复的时间（秒）")
    @TableField("wait_time_seconds")
    private Integer waitTimeSeconds;

    @Schema(description = "手势提示：point_mouth/point_stomach等")
    @TableField("gesture_hint")
    private String gestureHint;

    @Schema(description = "音效文件名")
    @TableField("music_effect")
    private String musicEffect;

    @Schema(description = "是否可选步骤：0-必需 1-可选")
    @TableField("is_optional")
    private Integer isOptional;

    @Schema(description = "步骤类型：normal/start/end/branch")
    @TableField("step_type")
    private String stepType;

    @Schema(description = "分支条件，JSON格式")
    @TableField("branch_condition")
    private String branchCondition;

    // 继承自BaseEntity的字段：id, creator, createDate
    // 需要单独定义的字段：
    @Schema(description = "更新者ID")
    @TableField("updater")
    private Long updater;

    @Schema(description = "更新时间")
    @TableField("update_date")
    private Date updateDate;

    // 扩展字段，用于前端显示
    @Schema(description = "场景名称")
    @TableField(exist = false)
    private String scenarioName;

    @Schema(description = "下一步骤名称")
    @TableField(exist = false)
    private String nextStepName;

    @Schema(description = "重试步骤名称")
    @TableField(exist = false)
    private String retryStepName;
} 