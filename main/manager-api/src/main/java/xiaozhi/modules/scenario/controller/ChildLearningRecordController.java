package xiaozhi.modules.scenario.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.scenario.entity.ChildLearningRecordEntity;
import xiaozhi.modules.scenario.service.ChildLearningRecordService;

import java.util.List;
import java.util.Map;

/**
 * 儿童学习记录管理
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@RestController
@RequestMapping("/xiaozhi/learning-record")
@Tag(name = "儿童学习记录管理")
public class ChildLearningRecordController {

    @Autowired
    private ChildLearningRecordService learningRecordService;

    @GetMapping("/list")
    @Operation(summary = "获取学习记录列表")
    public Result<PageData<ChildLearningRecordEntity>> list(@RequestParam Map<String, Object> params) {
        PageData<ChildLearningRecordEntity> page = learningRecordService.page(params);
        return new Result<PageData<ChildLearningRecordEntity>>().ok(page);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取学习记录详情")
    public Result<ChildLearningRecordEntity> get(@PathVariable("id") String id) {
        ChildLearningRecordEntity data = learningRecordService.getById(Long.valueOf(id));
        return new Result<ChildLearningRecordEntity>().ok(data);
    }

    @PostMapping
    @Operation(summary = "保存学习记录")
    public Result save(@RequestBody ChildLearningRecordEntity entity) {
        learningRecordService.saveLearningRecord(entity);
        return new Result();
    }

    @PutMapping("/{id}")
    @Operation(summary = "更新学习记录")
    public Result update(@PathVariable("id") String id, @RequestBody ChildLearningRecordEntity entity) {
        entity.setId(Long.valueOf(id));
        learningRecordService.updateLearningRecord(entity);
        return new Result();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除学习记录")
    public Result delete(@PathVariable("id") String id) {
        learningRecordService.removeById(Long.valueOf(id));
        return new Result();
    }

    @GetMapping("/agent/{agentId}")
    @Operation(summary = "根据智能体ID获取学习记录")
    public Result<List<ChildLearningRecordEntity>> getByAgentId(@PathVariable("agentId") String agentId) {
        List<ChildLearningRecordEntity> list = learningRecordService.getByAgentId(agentId);
        return new Result<List<ChildLearningRecordEntity>>().ok(list);
    }

    @GetMapping("/scenario/{scenarioId}")
    @Operation(summary = "根据场景ID获取学习记录")
    public Result<List<ChildLearningRecordEntity>> getByScenarioId(@PathVariable("scenarioId") String scenarioId) {
        List<ChildLearningRecordEntity> list = learningRecordService.getByScenarioId(scenarioId);
        return new Result<List<ChildLearningRecordEntity>>().ok(list);
    }

    @GetMapping("/child/{childName}")
    @Operation(summary = "根据儿童姓名获取学习记录")
    public Result<List<ChildLearningRecordEntity>> getByChildName(@PathVariable("childName") String childName) {
        List<ChildLearningRecordEntity> list = learningRecordService.getByChildName(childName);
        return new Result<List<ChildLearningRecordEntity>>().ok(list);
    }

    @GetMapping("/statistics")
    @Operation(summary = "获取学习统计信息")
    public Result<ChildLearningRecordEntity> getStatistics(@RequestParam String agentId, @RequestParam String childName) {
        ChildLearningRecordEntity statistics = learningRecordService.getStatistics(agentId, childName);
        return new Result<ChildLearningRecordEntity>().ok(statistics);
    }
}
