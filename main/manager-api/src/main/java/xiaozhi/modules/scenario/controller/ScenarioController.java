package xiaozhi.modules.scenario.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.scenario.entity.ScenarioEntity;
import xiaozhi.modules.scenario.service.ScenarioService;

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
@RequestMapping("/scenario")
@Tag(name = "场景配置管理")
@Slf4j
public class ScenarioController {

    @Autowired
    private ScenarioService scenarioService;

    @GetMapping("/list")
    @Operation(summary = "获取场景列表")
    public Result<PageData<ScenarioEntity>> list(@RequestParam Map<String, Object> params) {
        try {
            log.info("获取场景列表，参数: {}", params);
            PageData<ScenarioEntity> page = scenarioService.page(params);
            log.info("场景列表查询结果: total={}, list.size={}", page.getTotal(), page.getList() != null ? page.getList().size() : 0);
            if (page.getList() != null && !page.getList().isEmpty()) {
                log.info("第一个场景数据: {}", page.getList().get(0));
            }
            return new Result<PageData<ScenarioEntity>>().ok(page);
        } catch (Exception e) {
            log.error("获取场景列表异常", e);
            return new Result<PageData<ScenarioEntity>>().error("获取场景列表失败: " + e.getMessage());
        }
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取场景详情")
    public Result<ScenarioEntity> get(@PathVariable("id") String id) {
        try {
            log.info("获取场景详情，场景ID: {}", id);
            
            if (!StringUtils.hasText(id)) {
                log.warn("场景ID为空");
                return new Result<ScenarioEntity>().error("场景ID不能为空");
            }
            
            ScenarioEntity data = scenarioService.getById(Long.valueOf(id));
            if (data == null) {
                log.warn("场景不存在，场景ID: {}", id);
                return new Result<ScenarioEntity>().error("场景不存在");
            }
            
            log.info("获取场景详情成功，场景ID: {}, 场景名称: {}", id, data.getScenarioName());
            return new Result<ScenarioEntity>().ok(data);
            
        } catch (NumberFormatException e) {
            log.error("场景ID格式错误，场景ID: {}", id, e);
            return new Result<ScenarioEntity>().error("场景ID格式错误");
        } catch (Exception e) {
            log.error("获取场景详情异常，场景ID: {}", id, e);
            return new Result<ScenarioEntity>().error("获取场景详情失败: " + e.getMessage());
        }
    }

    @PostMapping
    @Operation(summary = "保存场景")
    public Result save(@RequestBody ScenarioEntity entity) {
        try {
            log.info("保存场景，场景名称: {}", entity.getScenarioName());
            
            if (entity == null) {
                log.warn("场景数据为空");
                return new Result().error("场景数据不能为空");
            }
            
            if (!StringUtils.hasText(entity.getScenarioName())) {
                log.warn("场景名称为空");
                return new Result().error("场景名称不能为空");
            }
            
            scenarioService.saveScenario(entity);
            log.info("保存场景成功，场景ID: {}", entity.getId());
            return new Result().ok("保存成功");
            
        } catch (Exception e) {
            log.error("保存场景异常", e);
            return new Result().error("保存失败: " + e.getMessage());
        }
    }

    @PutMapping("/{id}")
    @Operation(summary = "更新场景")
    public Result update(@PathVariable("id") String id, @RequestBody ScenarioEntity entity) {
        try {
            log.info("更新场景，场景ID: {}", id);
            
            if (!StringUtils.hasText(id)) {
                log.warn("场景ID为空");
                return new Result().error("场景ID不能为空");
            }
            
            if (entity == null) {
                log.warn("场景数据为空");
                return new Result().error("场景数据不能为空");
            }
            
            entity.setId(Long.valueOf(id));
            scenarioService.updateScenario(entity);
            log.info("更新场景成功，场景ID: {}", id);
            return new Result().ok("更新成功");
            
        } catch (NumberFormatException e) {
            log.error("场景ID格式错误，场景ID: {}", id, e);
            return new Result().error("场景ID格式错误");
        } catch (Exception e) {
            log.error("更新场景异常，场景ID: {}", id, e);
            return new Result().error("更新失败: " + e.getMessage());
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除场景")
    public Result delete(@PathVariable("id") String id) {
        try {
            log.info("删除场景，场景ID: {}", id);
            
            if (!StringUtils.hasText(id)) {
                log.warn("场景ID为空");
                return new Result().error("场景ID不能为空");
            }
            
            scenarioService.deleteScenario(id);
            log.info("删除场景成功，场景ID: {}", id);
            return new Result().ok("删除成功");
            
        } catch (Exception e) {
            log.error("删除场景异常，场景ID: {}", id, e);
            return new Result().error("删除失败: " + e.getMessage());
        }
    }

    @PutMapping("/{id}/toggle")
    @Operation(summary = "启用/禁用场景")
    public Result toggle(@PathVariable("id") String id, @RequestBody Map<String, Object> params) {
        try {
            log.info("切换场景状态，场景ID: {}, 参数: {}", id, params);
            
            if (!StringUtils.hasText(id)) {
                log.warn("场景ID为空");
                return new Result().error("场景ID不能为空");
            }
            
            Integer isActive = (Integer) params.get("isActive");
            if (isActive == null) {
                log.warn("启用状态参数为空");
                return new Result().error("启用状态参数不能为空");
            }
            
            scenarioService.toggleScenario(id, isActive);
            log.info("切换场景状态成功，场景ID: {}, 状态: {}", id, isActive);
            return new Result().ok("状态更新成功");
            
        } catch (Exception e) {
            log.error("切换场景状态异常，场景ID: {}", id, e);
            return new Result().error("状态更新失败: " + e.getMessage());
        }
    }

    @GetMapping("/agent/{agentId}")
    @Operation(summary = "根据智能体ID获取场景列表")
    public Result<List<ScenarioEntity>> getByAgentId(@PathVariable("agentId") String agentId) {
        try {
            log.info("根据智能体ID获取场景列表，智能体ID: {}", agentId);
            
            if (!StringUtils.hasText(agentId)) {
                log.warn("智能体ID为空");
                return new Result<List<ScenarioEntity>>().error("智能体ID不能为空");
            }
            
            List<ScenarioEntity> list = scenarioService.getByAgentId(agentId);
            log.info("获取场景列表成功，智能体ID: {}, 场景数量: {}", agentId, list != null ? list.size() : 0);
            return new Result<List<ScenarioEntity>>().ok(list);
            
        } catch (Exception e) {
            log.error("根据智能体ID获取场景列表异常，智能体ID: {}", agentId, e);
            return new Result<List<ScenarioEntity>>().error("获取场景列表失败: " + e.getMessage());
        }
    }

    @GetMapping("/active/{scenarioType}")
    @Operation(summary = "根据场景类型获取活跃场景列表")
    public Result<List<ScenarioEntity>> getActiveByType(@PathVariable("scenarioType") String scenarioType) {
        try {
            log.info("根据场景类型获取活跃场景列表，场景类型: {}", scenarioType);
            
            if (!StringUtils.hasText(scenarioType)) {
                log.warn("场景类型为空");
                return new Result<List<ScenarioEntity>>().error("场景类型不能为空");
            }
            
            List<ScenarioEntity> list = scenarioService.getActiveByType(scenarioType);
            log.info("获取活跃场景列表成功，场景类型: {}, 场景数量: {}", scenarioType, list != null ? list.size() : 0);
            return new Result<List<ScenarioEntity>>().ok(list);
            
        } catch (Exception e) {
            log.error("根据场景类型获取活跃场景列表异常，场景类型: {}", scenarioType, e);
            return new Result<List<ScenarioEntity>>().error("获取活跃场景列表失败: " + e.getMessage());
        }
    }

    @GetMapping("/test")
    @Operation(summary = "测试场景查询")
    public Result<String> test() {
        try {
            log.info("执行场景查询测试");
            Map<String, Object> params = new HashMap<>();
            params.put("page", 1);
            params.put("limit", 10);
            PageData<ScenarioEntity> page = scenarioService.page(params);
            String result = "查询成功: total=" + page.getTotal() + ", list.size=" + (page.getList() != null ? page.getList().size() : 0);
            log.info("场景查询测试结果: {}", result);
            return new Result<String>().ok(result);
        } catch (Exception e) {
            log.error("测试查询失败", e);
            return new Result<String>().error("测试查询失败: " + e.getMessage());
        }
    }
} 