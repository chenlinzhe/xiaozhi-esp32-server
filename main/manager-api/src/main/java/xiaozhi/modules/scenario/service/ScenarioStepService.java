package xiaozhi.modules.scenario.service;

import com.baomidou.mybatisplus.extension.service.IService;
import xiaozhi.modules.scenario.entity.ScenarioStepEntity;

import java.util.List;

/**
 * 对话步骤配置Service接口
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
public interface ScenarioStepService extends IService<ScenarioStepEntity> {

    /**
     * 根据场景ID获取步骤列表
     * 
     * @param scenarioId 场景ID
     * @return 步骤列表
     */
    List<ScenarioStepEntity> getStepsByScenarioId(String scenarioId);

    /**
     * 根据场景ID获取步骤列表（按顺序排序）
     * 
     * @param scenarioId 场景ID
     * @return 步骤列表
     */
    List<ScenarioStepEntity> getStepsByScenarioIdOrdered(String scenarioId);

    /**
     * 批量保存场景步骤
     * 
     * @param scenarioId 场景ID
     * @param steps 步骤列表
     * @return 是否成功
     */
    boolean batchSaveSteps(String scenarioId, List<ScenarioStepEntity> steps);

    /**
     * 删除场景的所有步骤
     * 
     * @param scenarioId 场景ID
     * @return 删除数量
     */
    int deleteStepsByScenarioId(String scenarioId);

    /**
     * 获取步骤数量
     * 
     * @param scenarioId 场景ID
     * @return 步骤数量
     */
    int countStepsByScenarioId(String scenarioId);
}
