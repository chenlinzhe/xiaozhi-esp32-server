package xiaozhi.modules.scenario.service;

import com.baomidou.mybatisplus.extension.service.IService;
import xiaozhi.modules.scenario.entity.StepTemplateEntity;

import java.util.List;

/**
 * 步骤模板Service接口
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
public interface StepTemplateService extends IService<StepTemplateEntity> {

    /**
     * 根据模板类型获取模板列表
     * 
     * @param templateType 模板类型
     * @return 模板列表
     */
    List<StepTemplateEntity> getByType(String templateType);

    /**
     * 获取默认模板列表
     * 
     * @return 默认模板列表
     */
    List<StepTemplateEntity> getDefaultTemplates();

    /**
     * 根据模板类型获取默认模板
     * 
     * @param templateType 模板类型
     * @return 默认模板
     */
    StepTemplateEntity getDefaultByType(String templateType);

    /**
     * 保存模板
     * 
     * @param entity 模板实体
     * @return 是否成功
     */
    boolean saveTemplate(StepTemplateEntity entity);

    /**
     * 更新模板
     * 
     * @param entity 模板实体
     * @return 是否成功
     */
    boolean updateTemplate(StepTemplateEntity entity);
}
