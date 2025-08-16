package xiaozhi.modules.scenario.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import xiaozhi.modules.scenario.dao.ScenarioStepMapper;
import xiaozhi.modules.scenario.entity.ScenarioStepEntity;
import xiaozhi.modules.scenario.service.ScenarioStepService;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.UUID;

/**
 * 对话步骤配置Service实现类
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Service
@Slf4j
public class ScenarioStepServiceImpl extends ServiceImpl<ScenarioStepMapper, ScenarioStepEntity> implements ScenarioStepService {

    @Override
    public List<ScenarioStepEntity> getStepsByScenarioId(String scenarioId) {
        try {
            log.info("获取场景步骤，场景ID: {}", scenarioId);
            List<ScenarioStepEntity> steps = baseMapper.selectByScenarioId(scenarioId);
            log.info("获取到步骤数量: {}", steps != null ? steps.size() : 0);
            return steps;
        } catch (Exception e) {
            log.error("获取场景步骤失败，场景ID: {}", scenarioId, e);
            return null;
        }
    }

    @Override
    public List<ScenarioStepEntity> getStepsByScenarioIdOrdered(String scenarioId) {
        try {
            log.info("获取场景步骤（有序），场景ID: {}", scenarioId);
            List<ScenarioStepEntity> steps = baseMapper.selectByScenarioIdOrdered(scenarioId);
            log.info("获取到步骤数量: {}", steps != null ? steps.size() : 0);
            return steps;
        } catch (Exception e) {
            log.error("获取场景步骤（有序）失败，场景ID: {}", scenarioId, e);
            return null;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean batchSaveSteps(String scenarioId, List<ScenarioStepEntity> steps) {
        try {
            log.info("批量保存步骤，场景ID: {}, 步骤数量: {}", scenarioId, steps != null ? steps.size() : 0);
            
            // 先删除原有步骤
            int deletedCount = baseMapper.deleteByScenarioId(scenarioId);
            log.info("删除原有步骤数量: {}", deletedCount);
            
            // 批量保存新步骤
            if (steps != null && !steps.isEmpty()) {
                for (int i = 0; i < steps.size(); i++) {
                    ScenarioStepEntity step = steps.get(i);
                    step.setScenarioId(scenarioId);
                    step.setStepOrder(i + 1);
                    
                    // 生成步骤ID
                    if (step.getStepId() == null || step.getStepId().trim().isEmpty()) {
                        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
                        String uuid = UUID.randomUUID().toString().substring(0, 8);
                        step.setStepId("STEP_" + timestamp + "_" + uuid);
                    }
                    
                    // 生成步骤编码
                    if (step.getStepCode() == null || step.getStepCode().isEmpty()) {
                        step.setStepCode("step_" + (i + 1));
                    }
                    
                    save(step);
                }
                log.info("批量保存步骤成功");
            }
            
            return true;
        } catch (Exception e) {
            log.error("批量保存步骤失败，场景ID: {}", scenarioId, e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int deleteStepsByScenarioId(String scenarioId) {
        try {
            log.info("删除场景步骤，场景ID: {}", scenarioId);
            int count = baseMapper.deleteByScenarioId(scenarioId);
            log.info("删除步骤数量: {}", count);
            return count;
        } catch (Exception e) {
            log.error("删除场景步骤失败，场景ID: {}", scenarioId, e);
            return 0;
        }
    }

    @Override
    public int countStepsByScenarioId(String scenarioId) {
        try {
            int count = baseMapper.countByScenarioId(scenarioId);
            log.debug("场景步骤数量，场景ID: {}, 数量: {}", scenarioId, count);
            return count;
        } catch (Exception e) {
            log.error("统计场景步骤数量失败，场景ID: {}", scenarioId, e);
            return 0;
        }
    }
}
