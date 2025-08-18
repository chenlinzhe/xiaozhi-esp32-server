package xiaozhi.modules.scenario.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import xiaozhi.modules.scenario.entity.StepTemplateEntity;

import java.util.List;

/**
 * 步骤模板Mapper接口
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Mapper
public interface StepTemplateMapper extends BaseMapper<StepTemplateEntity> {

    /**
     * 根据模板类型获取模板列表
     * 
     * @param templateType 模板类型
     * @return 模板列表
     */
    List<StepTemplateEntity> selectByType(@Param("templateType") String templateType);

    /**
     * 获取默认模板列表
     * 
     * @return 默认模板列表
     */
    List<StepTemplateEntity> selectDefaultTemplates();

    /**
     * 根据模板类型获取默认模板
     * 
     * @param templateType 模板类型
     * @return 默认模板
     */
    StepTemplateEntity selectDefaultByType(@Param("templateType") String templateType);
} 