package xiaozhi.modules.scenario.service;

import com.baomidou.mybatisplus.extension.service.IService;
import xiaozhi.modules.scenario.entity.StepMessageEntity;

import java.util.List;

/**
 * 步骤AI消息Service接口
 * 
 * @author xiaozhi
 * @since 2025-01-01
 */
public interface StepMessageService extends IService<StepMessageEntity> {

    /**
     * 根据步骤ID获取消息列表
     * 
     * @param stepId 步骤ID
     * @return 消息列表
     */
    List<StepMessageEntity> getMessagesByStepId(String stepId);

    /**
     * 根据步骤ID获取消息列表（按顺序排序）
     * 
     * @param stepId 步骤ID
     * @return 消息列表
     */
    List<StepMessageEntity> getMessagesByStepIdOrdered(String stepId);

    /**
     * 根据场景ID获取所有消息
     * 
     * @param scenarioId 场景ID
     * @return 消息列表
     */
    List<StepMessageEntity> getMessagesByScenarioId(String scenarioId);

    /**
     * 批量保存步骤消息
     * 
     * @param stepId 步骤ID
     * @param messages 消息列表
     * @return 是否成功
     */
    boolean batchSaveMessages(String stepId, List<StepMessageEntity> messages);

    /**
     * 删除步骤的所有消息
     * 
     * @param stepId 步骤ID
     * @return 删除数量
     */
    int deleteMessagesByStepId(String stepId);

    /**
     * 删除场景的所有消息
     * 
     * @param scenarioId 场景ID
     * @return 删除数量
     */
    int deleteMessagesByScenarioId(String scenarioId);

    /**
     * 获取步骤消息数量
     * 
     * @param stepId 步骤ID
     * @return 消息数量
     */
    int countMessagesByStepId(String stepId);

    /**
     * 重新排序消息
     * 
     * @param stepId 步骤ID
     * @param messageOrders 消息顺序列表
     * @return 是否成功
     */
    boolean reorderMessages(String stepId, List<StepMessageEntity> messageOrders);
}
