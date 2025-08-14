package xiaozhi.modules.scenario.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.scenario.entity.ScenarioEntity;
import xiaozhi.modules.scenario.service.ScenarioService;
import lombok.extern.slf4j.Slf4j;

import java.util.HashMap;
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
@Slf4j
public class ScenarioController {

    @Autowired
    private ScenarioService scenarioService;

    @GetMapping("/list")
    @Operation(summary = "获取场景列表")
    public Result<PageData<ScenarioEntity>> list(@RequestParam Map<String, Object> params) {
        log.info("获取场景列表，参数: {}", params);
        PageData<ScenarioEntity> page = scenarioService.page(params);
        log.info("场景列表查询结果: total={}, list.size={}", page.getTotal(), page.getList() != null ? page.getList().size() : 0);
        if (page.getList() != null && !page.getList().isEmpty()) {
            log.info("第一个场景数据: {}", page.getList().get(0));
        }
        return new Result<PageData<ScenarioEntity>>().ok(page);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取场景详情")
    public Result<ScenarioEntity> get(@PathVariable("id") String id) {
        ScenarioEntity data = scenarioService.getById(Long.valueOf(id));
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
        entity.setId(Long.valueOf(id));
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
    public Result toggle(@PathVariable("id") String id, @RequestBody Map<String, Object> params) {
        Integer isActive = (Integer) params.get("isActive");
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

    @GetMapping("/test")
    @Operation(summary = "测试场景查询")
    public Result<String> test() {
        try {
            Map<String, Object> params = new HashMap<>();
            params.put("page", 1);
            params.put("limit", 10);
            PageData<ScenarioEntity> page = scenarioService.page(params);
            return new Result<String>().ok("查询成功: total=" + page.getTotal() + ", list.size=" + (page.getList() != null ? page.getList().size() : 0));
        } catch (Exception e) {
            log.error("测试查询失败", e);
            return new Result<String>().error("测试查询失败: " + e.getMessage());
        }
    }
} 