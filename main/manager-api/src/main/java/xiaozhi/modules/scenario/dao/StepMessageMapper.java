package xiaozhi.modules.scenario.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import xiaozhi.modules.scenario.entity.StepMessageEntity;

import java.util.List;

/**
 * 步骤AI消息Mapper接口
 * 
 * @author xiaozhi
 * @since 2025-01-01
 */
@Mapper
public interface StepMessageMapper extends BaseMapper<StepMessageEntity> {

    /**
     * 根据步骤ID获取消息列表
     * 
     * @param stepId 步骤ID
     * @return 消息列表
     */
    List<StepMessageEntity> selectByStepId(@Param("stepId") String stepId);

    /**
     * 根据步骤ID获取消息列表（按顺序排序）
     * 
     * @param stepId stepId
     * @return 消息列表
     */
    List<StepMessageEntity> selectByStepIdOrdered(@Param("stepId") String stepId);

    /**
     * 根据场景ID获取所有消息
     * 
     * @param scenarioId 场景ID
     * @return 消息列表
     */
    List<StepMessageEntity> selectByScenarioId(@Param("scenarioId") String scenarioId);

    /**
     * 批量删除步骤消息
     * 
     * @param stepId 步骤ID
     * @return 删除数量
     */
    int deleteByStepId(@Param("stepId") String stepId);

    /**
     * 批量删除场景消息
     * 
     * @param scenarioId 场景ID
     * @return 删除数量
     */
    int deleteByScenarioId(@Param("scenarioId") String scenarioId);

    /**
     * 获取步骤消息数量
     * 
     * @param stepId 步骤ID
     * @return 消息数量
     */
    int countByStepId(@Param("stepId") String stepId);
}
