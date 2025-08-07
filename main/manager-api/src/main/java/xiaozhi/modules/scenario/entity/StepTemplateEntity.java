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

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "模板唯一标识")
    private String id;

    @Schema(description = "模板编码")
    private String templateCode;

    @Schema(description = "模板名称")
    private String templateName;

    @Schema(description = "模板类型：greeting/instruction/encouragement等")
    private String templateType;

    @Schema(description = "AI说的话模板")
    private String aiMessage;

    @Schema(description = "期望的关键词模板")
    private String expectedKeywords;

    @Schema(description = "期望的完整短语模板")
    private String expectedPhrases;

    @Schema(description = "替代提示模板")
    private String alternativeMessage;

    @Schema(description = "模板描述")
    private String description;

    @Schema(description = "是否默认模板")
    private Integer isDefault;

    @Schema(description = "排序权重")
    private Integer sortOrder;

    @Schema(description = "创建者ID")
    private Long creator;

    @Schema(description = "创建时间")
    private Date createdAt;
} 