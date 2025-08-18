package xiaozhi.modules.scenario.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import xiaozhi.modules.scenario.entity.ChildLearningRecordEntity;

import java.util.List;

/**
 * 儿童学习记录Mapper接口
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Mapper
public interface ChildLearningRecordMapper extends BaseMapper<ChildLearningRecordEntity> {

    /**
     * 根据智能体ID获取学习记录
     * 
     * @param agentId 智能体ID
     * @return 学习记录列表
     */
    List<ChildLearningRecordEntity> selectByAgentId(@Param("agentId") String agentId);

    /**
     * 根据场景ID获取学习记录
     * 
     * @param scenarioId 场景ID
     * @return 学习记录列表
     */
    List<ChildLearningRecordEntity> selectByScenarioId(@Param("scenarioId") String scenarioId);

    /**
     * 根据儿童姓名获取学习记录
     * 
     * @param childName 儿童姓名
     * @return 学习记录列表
     */
    List<ChildLearningRecordEntity> selectByChildName(@Param("childName") String childName);

    /**
     * 获取学习统计信息
     * 
     * @param agentId 智能体ID
     * @param childName 儿童姓名
     * @return 统计信息
     */
    ChildLearningRecordEntity selectStatistics(@Param("agentId") String agentId, 
                                              @Param("childName") String childName);
} 