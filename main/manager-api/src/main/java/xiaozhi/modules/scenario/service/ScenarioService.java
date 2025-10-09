package xiaozhi.modules.scenario.service;

import com.baomidou.mybatisplus.extension.service.IService;
import xiaozhi.common.page.PageData;
import xiaozhi.modules.scenario.entity.ScenarioEntity;

import java.util.List;
import java.util.Map;

/**
 * 场景配置Service接口
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
public interface ScenarioService extends IService<ScenarioEntity> {

    /**
     * 分页查询场景列表
     * 
     * @param params 查询参数
     * @return 分页数据
     */
    PageData<ScenarioEntity> page(Map<String, Object> params);

    /**
     * 根据智能体ID获取场景列表
     * 
     * @param agentId 智能体ID
     * @return 场景列表
     */
    List<ScenarioEntity> getByAgentId(String agentId);

    /**
     * 根据场景类型获取活跃场景列表
     * 
     * @param scenarioType 场景类型
     * @return 场景列表
     */
    List<ScenarioEntity> getActiveByType(String scenarioType);

    /**
     * 保存场景配置
     * 
     * @param entity 场景实体
     * @return 是否成功
     */
    boolean saveScenario(ScenarioEntity entity);

    /**
     * 更新场景配置
     * 
     * @param entity 场景实体
     * @return 是否成功
     */
    boolean updateScenario(ScenarioEntity entity);

    /**
     * 删除场景配置
     * 
     * @param id 场景ID
     * @return 是否成功
     */
    boolean deleteScenario(String id);

    /**
     * 启用/禁用场景
     * 
     * @param id 场景ID
     * @param isActive 是否启用
     * @return 是否成功
     */
    boolean toggleScenario(String id, Integer isActive);
} 