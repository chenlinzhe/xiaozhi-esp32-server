package xiaozhi.modules.scenario.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.scenario.entity.StepTemplateEntity;
import xiaozhi.modules.scenario.service.StepTemplateService;

import java.util.List;

/**
 * 步骤模板管理
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@RestController
@RequestMapping("/xiaozhi/step-template")
@Tag(name = "步骤模板管理")
public class StepTemplateController {

    @Autowired
    private StepTemplateService templateService;

    @GetMapping("/list")
    @Operation(summary = "获取模板列表")
    public Result<List<StepTemplateEntity>> list() {
        List<StepTemplateEntity> list = templateService.list();
        return new Result<List<StepTemplateEntity>>().ok(list);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取模板详情")
    public Result<StepTemplateEntity> get(@PathVariable("id") String id) {
        StepTemplateEntity data = templateService.getById(id);
        return new Result<StepTemplateEntity>().ok(data);
    }

    @PostMapping
    @Operation(summary = "保存模板")
    public Result save(@RequestBody StepTemplateEntity entity) {
        templateService.saveTemplate(entity);
        return new Result();
    }

    @PutMapping("/{id}")
    @Operation(summary = "更新模板")
    public Result update(@PathVariable("id") String id, @RequestBody StepTemplateEntity entity) {
        entity.setId(id);
        templateService.updateTemplate(entity);
        return new Result();
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除模板")
    public Result delete(@PathVariable("id") String id) {
        templateService.removeById(id);
        return new Result();
    }

    @GetMapping("/type/{templateType}")
    @Operation(summary = "根据类型获取模板列表")
    public Result<List<StepTemplateEntity>> getByType(@PathVariable("templateType") String templateType) {
        List<StepTemplateEntity> list = templateService.getByType(templateType);
        return new Result<List<StepTemplateEntity>>().ok(list);
    }

    @GetMapping("/default")
    @Operation(summary = "获取默认模板列表")
    public Result<List<StepTemplateEntity>> getDefaultTemplates() {
        List<StepTemplateEntity> list = templateService.getDefaultTemplates();
        return new Result<List<StepTemplateEntity>>().ok(list);
    }

    @GetMapping("/default/{templateType}")
    @Operation(summary = "根据类型获取默认模板")
    public Result<StepTemplateEntity> getDefaultByType(@PathVariable("templateType") String templateType) {
        StepTemplateEntity template = templateService.getDefaultByType(templateType);
        return new Result<StepTemplateEntity>().ok(template);
    }
}
