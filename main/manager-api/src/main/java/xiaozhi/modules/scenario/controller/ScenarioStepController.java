package xiaozhi.modules.scenario.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.scenario.entity.ScenarioStepEntity;
import xiaozhi.modules.scenario.service.ScenarioStepService;

import java.util.List;

/**
 * 场景步骤管理
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@RestController
@RequestMapping("/xiaozhi/scenario-step")
@Tag(name = "场景步骤管理")
@Slf4j
public class ScenarioStepController {

    @Autowired
    private ScenarioStepService stepService;

    @GetMapping("/list/{scenarioId}")
    @Operation(summary = "获取场景步骤列表")
    public Result<List<ScenarioStepEntity>> getStepsByScenario(@PathVariable("scenarioId") String scenarioId) {
        try {
            log.info("获取场景步骤列表，场景ID: {}", scenarioId);
            
            if (!StringUtils.hasText(scenarioId)) {
                log.warn("场景ID为空");
                return new Result<List<ScenarioStepEntity>>().error("场景ID不能为空");
            }
            
            List<ScenarioStepEntity> steps = stepService.getStepsByScenarioIdOrdered(scenarioId);
            
            if (steps == null) {
                log.error("获取场景步骤失败，场景ID: {}", scenarioId);
                return new Result<List<ScenarioStepEntity>>().error("获取场景步骤失败");
            }
            
            log.info("获取场景步骤成功，场景ID: {}, 步骤数量: {}", scenarioId, steps.size());
            return new Result<List<ScenarioStepEntity>>().ok(steps);
            
        } catch (Exception e) {
            log.error("获取场景步骤列表异常，场景ID: {}", scenarioId, e);
            return new Result<List<ScenarioStepEntity>>().error("获取场景步骤列表失败: " + e.getMessage());
        }
    }

    @PostMapping("/batch-save/{scenarioId}")
    @Operation(summary = "批量保存场景步骤")
    public Result batchSave(@PathVariable("scenarioId") String scenarioId, 
                           @RequestBody List<ScenarioStepEntity> steps) {
        try {
            log.info("批量保存场景步骤，场景ID: {}, 步骤数量: {}", scenarioId, steps != null ? steps.size() : 0);
            
            if (!StringUtils.hasText(scenarioId)) {
                log.warn("场景ID为空");
                return new Result().error("场景ID不能为空");
            }
            
            if (steps == null) {
                log.warn("步骤数据为空");
                return new Result().error("步骤数据不能为空");
            }
            
            boolean success = stepService.batchSaveSteps(scenarioId, steps);
            if (success) {
                log.info("批量保存场景步骤成功，场景ID: {}", scenarioId);
                return new Result().ok("保存成功");
            } else {
                log.error("批量保存场景步骤失败，场景ID: {}", scenarioId);
                return new Result().error("保存失败");
            }
            
        } catch (Exception e) {
            log.error("批量保存场景步骤异常，场景ID: {}", scenarioId, e);
            return new Result().error("保存失败: " + e.getMessage());
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除步骤")
    public Result delete(@PathVariable("id") String id) {
        try {
            log.info("删除步骤，步骤ID: {}", id);
            
            if (!StringUtils.hasText(id)) {
                log.warn("步骤ID为空");
                return new Result().error("步骤ID不能为空");
            }
            
            stepService.removeById(Long.valueOf(id));
            log.info("删除步骤成功，步骤ID: {}", id);
            return new Result().ok("删除成功");
            
        } catch (Exception e) {
            log.error("删除步骤异常，步骤ID: {}", id, e);
            return new Result().error("删除失败: " + e.getMessage());
        }
    }

    @GetMapping("/count/{scenarioId}")
    @Operation(summary = "获取场景步骤数量")
    public Result<Integer> countSteps(@PathVariable("scenarioId") String scenarioId) {
        try {
            log.info("获取场景步骤数量，场景ID: {}", scenarioId);
            
            if (!StringUtils.hasText(scenarioId)) {
                log.warn("场景ID为空");
                return new Result<Integer>().error("场景ID不能为空");
            }
            
            int count = stepService.countStepsByScenarioId(scenarioId);
            log.info("获取场景步骤数量成功，场景ID: {}, 数量: {}", scenarioId, count);
            return new Result<Integer>().ok(count);
            
        } catch (Exception e) {
            log.error("获取场景步骤数量异常，场景ID: {}", scenarioId, e);
            return new Result<Integer>().error("获取步骤数量失败: " + e.getMessage());
        }
    }
}
