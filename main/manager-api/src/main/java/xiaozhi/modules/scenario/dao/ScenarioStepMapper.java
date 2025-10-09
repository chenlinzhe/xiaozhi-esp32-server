package xiaozhi.modules.scenario.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import xiaozhi.modules.scenario.entity.ScenarioStepEntity;

import java.util.List;

/**
 * 对话步骤配置Mapper接口
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Mapper
public interface ScenarioStepMapper extends BaseMapper<ScenarioStepEntity> {

    /**
     * 根据场景ID获取步骤列表
     * 
     * @param scenarioId 场景ID
     * @return 步骤列表
     */
    List<ScenarioStepEntity> selectByScenarioId(@Param("scenarioId") String scenarioId);

    /**
     * 根据场景ID获取步骤列表（按顺序排序）
     * 
     * @param scenarioId 场景ID
     * @return 步骤列表
     */
    List<ScenarioStepEntity> selectByScenarioIdOrdered(@Param("scenarioId") String scenarioId);

    /**
     * 批量删除场景步骤
     * 
     * @param scenarioId 场景ID
     * @return 删除数量
     */
    int deleteByScenarioId(@Param("scenarioId") String scenarioId);

    /**
     * 获取步骤数量
     * 
     * @param scenarioId 场景ID
     * @return 步骤数量
     */
    int countByScenarioId(@Param("scenarioId") String scenarioId);
} 