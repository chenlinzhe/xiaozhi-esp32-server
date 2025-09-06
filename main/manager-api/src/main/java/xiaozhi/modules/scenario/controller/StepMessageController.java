package xiaozhi.modules.scenario.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.scenario.entity.StepMessageEntity;
import xiaozhi.modules.scenario.service.StepMessageService;

import java.util.List;

/**
 * 步骤AI消息管理
 * 
 * @author xiaozhi
 * @since 2025-01-01
 */
@RestController
@RequestMapping("/step-message")
@Tag(name = "步骤AI消息管理")
@Slf4j
public class StepMessageController {

    @Autowired
    private StepMessageService messageService;

    @GetMapping("/list/{stepId}")
    @Operation(summary = "获取步骤消息列表")
    public Result<List<StepMessageEntity>> getMessagesByStep(@PathVariable("stepId") String stepId) {
        try {
            log.info("获取步骤消息列表，步骤ID: {}", stepId);
            
            if (!StringUtils.hasText(stepId)) {
                log.warn("步骤ID为空");
                return new Result<List<StepMessageEntity>>().error("步骤ID不能为空");
            }
            
            List<StepMessageEntity> messages = messageService.getMessagesByStepIdOrdered(stepId);
            
            if (messages == null) {
                log.error("获取步骤消息失败，步骤ID: {}", stepId);
                return new Result<List<StepMessageEntity>>().error("获取步骤消息失败");
            }
            
            log.info("获取步骤消息成功，步骤ID: {}, 消息数量: {}", stepId, messages.size());
            return new Result<List<StepMessageEntity>>().ok(messages);
            
        } catch (Exception e) {
            log.error("获取步骤消息列表异常，步骤ID: {}", stepId, e);
            return new Result<List<StepMessageEntity>>().error("获取步骤消息列表失败: " + e.getMessage());
        }
    }

    @PostMapping("/batch-save/{stepId}")
    @Operation(summary = "批量保存步骤消息")
    public Result batchSave(@PathVariable("stepId") String stepId, 
                           @RequestBody List<StepMessageEntity> messages) {
        try {
            log.info("批量保存步骤消息，步骤ID: {}, 消息数量: {}", stepId, messages != null ? messages.size() : 0);
            
            if (!StringUtils.hasText(stepId)) {
                log.warn("步骤ID为空");
                return new Result().error("步骤ID不能为空");
            }
            
            boolean success = messageService.batchSaveMessages(stepId, messages);
            if (success) {
                log.info("批量保存步骤消息成功，步骤ID: {}", stepId);
                return new Result().ok("保存成功");
            } else {
                log.error("批量保存步骤消息失败，步骤ID: {}", stepId);
                return new Result().error("保存失败");
            }
            
        } catch (Exception e) {
            log.error("批量保存步骤消息异常，步骤ID: {}", stepId, e);
            return new Result().error("保存失败: " + e.getMessage());
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除消息")
    public Result delete(@PathVariable("id") String id) {
        try {
            log.info("删除消息，消息ID: {}", id);
            
            if (!StringUtils.hasText(id)) {
                log.warn("消息ID为空");
                return new Result().error("消息ID不能为空");
            }
            
            messageService.removeById(Long.valueOf(id));
            log.info("删除消息成功，消息ID: {}", id);
            return new Result().ok("删除成功");
            
        } catch (Exception e) {
            log.error("删除消息异常，消息ID: {}", id, e);
            return new Result().error("删除失败: " + e.getMessage());
        }
    }

    @GetMapping("/count/{stepId}")
    @Operation(summary = "获取步骤消息数量")
    public Result<Integer> countMessages(@PathVariable("stepId") String stepId) {
        try {
            log.info("获取步骤消息数量，步骤ID: {}", stepId);
            
            if (!StringUtils.hasText(stepId)) {
                log.warn("步骤ID为空");
                return new Result<Integer>().error("步骤ID不能为空");
            }
            
            int count = messageService.countMessagesByStepId(stepId);
            log.info("获取步骤消息数量成功，步骤ID: {}, 数量: {}", stepId, count);
            return new Result<Integer>().ok(count);
            
        } catch (Exception e) {
            log.error("获取步骤消息数量异常，步骤ID: {}", stepId, e);
            return new Result<Integer>().error("获取消息数量失败: " + e.getMessage());
        }
    }

    @PostMapping("/reorder/{stepId}")
    @Operation(summary = "重新排序消息")
    public Result reorderMessages(@PathVariable("stepId") String stepId, 
                                 @RequestBody List<StepMessageEntity> messageOrders) {
        try {
            log.info("重新排序消息，步骤ID: {}, 消息数量: {}", stepId, messageOrders != null ? messageOrders.size() : 0);
            
            if (!StringUtils.hasText(stepId)) {
                log.warn("步骤ID为空");
                return new Result().error("步骤ID不能为空");
            }
            
            boolean success = messageService.reorderMessages(stepId, messageOrders);
            if (success) {
                log.info("重新排序消息成功，步骤ID: {}", stepId);
                return new Result().ok("排序成功");
            } else {
                log.error("重新排序消息失败，步骤ID: {}", stepId);
                return new Result().error("排序失败");
            }
            
        } catch (Exception e) {
            log.error("重新排序消息异常，步骤ID: {}", stepId, e);
            return new Result().error("排序失败: " + e.getMessage());
        }
    }
}
