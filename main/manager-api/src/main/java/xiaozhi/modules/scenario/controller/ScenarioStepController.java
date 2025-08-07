package xiaozhi.modules.scenario.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
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
public class ScenarioStepController {

    @Autowired
    private ScenarioStepService stepService;

    @GetMapping("/list/{scenarioId}")
    @Operation(summary = "获取场景步骤列表")
    public Result<List<ScenarioStepEntity>> getStepsByScenario(@PathVariable("scenarioId") String scenarioId) {
        List<ScenarioStepEntity> steps = stepService.getStepsByScenarioIdOrdered(scenarioId);
        return new Result<List<ScenarioStepEntity>>().ok(steps);
    }

    @PostMapping("/batch-save/{scenarioId}")
    @Operation(summary = "批量保存场景步骤")
    public Result batchSave(@PathVariable("scenarioId") String scenarioId, 
                           @RequestBody List<ScenarioStepEntity> steps) {
        boolean success = stepService.batchSaveSteps(scenarioId, steps);
        if (success) {
            return new Result();
        } else {
            return new Result().error("保存失败");
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除步骤")
    public Result delete(@PathVariable("id") String id) {
        stepService.removeById(id);
        return new Result();
    }

    @GetMapping("/count/{scenarioId}")
    @Operation(summary = "获取场景步骤数量")
    public Result<Integer> countSteps(@PathVariable("scenarioId") String scenarioId) {
        int count = stepService.countStepsByScenarioId(scenarioId);
        return new Result<Integer>().ok(count);
    }
}
