package xiaozhi.modules.scenario.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.scenario.entity.ScenarioEntity;
import xiaozhi.modules.scenario.service.ScenarioService;

import java.util.List;
import java.util.Map;

/**
 * 场景配置管理
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@RestController
@RequestMapping("/xiaozhi/scenario")
@Tag(name = "场景配置管理")
public class ScenarioController {

    @Autowired
    private ScenarioService scenarioService;

    @GetMapping("/list")
    @Operation(summary = "获取场景列表")
    public Result<PageData<ScenarioEntity>> list(@RequestParam Map<String, Object> params) {
        PageData<ScenarioEntity> page = scenarioService.page(params);
        return new Result<PageData<ScenarioEntity>>().ok(page);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取场景详情")
    public Result<ScenarioEntity> get(@PathVariable("id") String id) {
        ScenarioEntity data = scenarioService.getById(id);
        return new Result<ScenarioEntity>().ok(data);
    }

    @PostMapping
    @Operation(summary = "保存场景")
    public Result save(@RequestBody ScenarioEntity entity) {
        scenarioService.saveScenario(entity);
        return new Result();
    }

    @PutMapping("/{id}")
    @Operation(summary = "更新场景")
    public Result update(@PathVariable("id") String id, @RequestBody ScenarioEntity entity) {
        entity.setId(id);
        scenarioService.updateScenario(entity);
        return new Result();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除场景")
    public Result delete(@PathVariable("id") String id) {
        scenarioService.deleteScenario(id);
        return new Result();
    }

    @PutMapping("/{id}/toggle")
    @Operation(summary = "启用/禁用场景")
    public Result toggle(@PathVariable("id") String id, @RequestParam Integer isActive) {
        scenarioService.toggleScenario(id, isActive);
        return new Result();
    }

    @GetMapping("/agent/{agentId}")
    @Operation(summary = "根据智能体ID获取场景列表")
    public Result<List<ScenarioEntity>> getByAgentId(@PathVariable("agentId") String agentId) {
        List<ScenarioEntity> list = scenarioService.getByAgentId(agentId);
        return new Result<List<ScenarioEntity>>().ok(list);
    }

    @GetMapping("/active/{scenarioType}")
    @Operation(summary = "根据场景类型获取活跃场景列表")
    public Result<List<ScenarioEntity>> getActiveByType(@PathVariable("scenarioType") String scenarioType) {
        List<ScenarioEntity> list = scenarioService.getActiveByType(scenarioType);
        return new Result<List<ScenarioEntity>>().ok(list);
    }
} 