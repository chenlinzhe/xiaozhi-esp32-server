package xiaozhi.modules.scenario.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import xiaozhi.modules.scenario.entity.ScenarioEntity;

import java.util.List;
import java.util.Map;

/**
 * 场景配置Mapper接口
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Mapper
public interface ScenarioMapper extends BaseMapper<ScenarioEntity> {

    /**
     * 根据智能体ID获取场景列表
     * 
     * @param agentId 智能体ID
     * @return 场景列表
     */
    List<ScenarioEntity> selectByAgentId(@Param("agentId") String agentId);

    /**
     * 获取场景列表（包含步骤数量）
     * 
     * @param params 查询参数
     * @return 场景列表
     */
    List<ScenarioEntity> selectScenarioList(Map<String, Object> params);

    /**
     * 获取场景列表总数
     * 
     * @param params 查询参数
     * @return 总数
     */
    long selectScenarioListCount(Map<String, Object> params);

    /**
     * 根据场景类型获取场景列表
     * 
     * @param scenarioType 场景类型
     * @param isActive 是否启用
     * @return 场景列表
     */
    List<ScenarioEntity> selectByTypeAndStatus(@Param("scenarioType") String scenarioType, 
                                              @Param("isActive") Integer isActive);
} 