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
 * 步骤模板实体类
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("ai_step_template")
@Schema(description = "步骤模板信息")
public class StepTemplateEntity extends BaseEntity {

    @Schema(description = "模板唯一标识")
    @TableField("template_id")
    private String templateId;

    @Schema(description = "模板编码")
    @TableField("template_code")
    private String templateCode;

    @Schema(description = "模板名称")
    @TableField("template_name")
    private String templateName;

    @Schema(description = "模板类型：greeting/instruction/encouragement等")
    @TableField("template_type")
    private String templateType;

    // 已删除AI消息字段，不再使用固定配置的语句

    @Schema(description = "期望的关键词模板")
    @TableField("expected_keywords")
    private String expectedKeywords;

    @Schema(description = "期望的完整短语模板")
    @TableField("expected_phrases")
    private String expectedPhrases;

    // 已删除替代消息字段，不再使用替代提示

    @Schema(description = "语速配置：0.5-2.0倍速，1.0为正常语速")
    @TableField("speech_rate")
    private BigDecimal speechRate;

    @Schema(description = "模板描述")
    @TableField("description")
    private String description;

    @Schema(description = "是否默认模板")
    @TableField("is_default")
    private Integer isDefault;

    @Schema(description = "排序权重")
    @TableField("sort_order")
    private Integer sortOrder;

    // 继承自BaseEntity的字段：id, creator, createDate
    // 注意：creator和createDate字段通过继承BaseEntity获得，不需要重复定义
} 