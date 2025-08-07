package xiaozhi.modules.scenario.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import xiaozhi.modules.scenario.dao.ScenarioStepMapper;
import xiaozhi.modules.scenario.entity.ScenarioStepEntity;
import xiaozhi.modules.scenario.service.ScenarioStepService;

import java.util.List;

/**
 * 对话步骤配置Service实现类
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Service
public class ScenarioStepServiceImpl extends ServiceImpl<ScenarioStepMapper, ScenarioStepEntity> implements ScenarioStepService {

    @Override
    public List<ScenarioStepEntity> getStepsByScenarioId(String scenarioId) {
        return baseMapper.selectByScenarioId(scenarioId);
    }

    @Override
    public List<ScenarioStepEntity> getStepsByScenarioIdOrdered(String scenarioId) {
        return baseMapper.selectByScenarioIdOrdered(scenarioId);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean batchSaveSteps(String scenarioId, List<ScenarioStepEntity> steps) {
        try {
            // 先删除原有步骤
            baseMapper.deleteByScenarioId(scenarioId);
            
            // 批量保存新步骤
            if (steps != null && !steps.isEmpty()) {
                for (int i = 0; i < steps.size(); i++) {
                    ScenarioStepEntity step = steps.get(i);
                    step.setScenarioId(scenarioId);
                    step.setStepOrder(i + 1);
                    
                    // 生成步骤编码
                    if (step.getStepCode() == null || step.getStepCode().isEmpty()) {
                        step.setStepCode("step_" + (i + 1));
                    }
                    
                    save(step);
                }
            }
            
            return true;
        } catch (Exception e) {
            log.error("批量保存步骤失败", e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int deleteStepsByScenarioId(String scenarioId) {
        return baseMapper.deleteByScenarioId(scenarioId);
    }

    @Override
    public int countStepsByScenarioId(String scenarioId) {
        return baseMapper.countByScenarioId(scenarioId);
    }
}
