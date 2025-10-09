package xiaozhi.modules.scenario.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import xiaozhi.modules.scenario.dao.StepMessageMapper;
import xiaozhi.modules.scenario.entity.StepMessageEntity;
import xiaozhi.modules.scenario.service.StepMessageService;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.UUID;

/**
 * 步骤AI消息Service实现类
 * 
 * @author xiaozhi
 * @since 2025-01-01
 */
@Service
@Slf4j
public class StepMessageServiceImpl extends ServiceImpl<StepMessageMapper, StepMessageEntity> implements StepMessageService {

    @Override
    public List<StepMessageEntity> getMessagesByStepId(String stepId) {
        try {
            log.info("获取步骤消息，步骤ID: {}", stepId);
            List<StepMessageEntity> messages = baseMapper.selectByStepId(stepId);
            log.info("获取到消息数量: {}", messages != null ? messages.size() : 0);
            return messages;
        } catch (Exception e) {
            log.error("获取步骤消息失败，步骤ID: {}", stepId, e);
            return null;
        }
    }

    @Override
    public List<StepMessageEntity> getMessagesByStepIdOrdered(String stepId) {
        try {
            log.info("获取步骤消息（有序），步骤ID: {}", stepId);
            List<StepMessageEntity> messages = baseMapper.selectByStepIdOrdered(stepId);
            log.info("获取到消息数量: {}", messages != null ? messages.size() : 0);
            return messages;

        } catch (Exception e) {
            log.error("获取步骤消息（有序）失败，步骤ID: {}", stepId, e);
            return null;
        }
    }

    @Override
    public List<StepMessageEntity> getMessagesByScenarioId(String scenarioId) {
        try {
            log.info("获取场景消息，场景ID: {}", scenarioId);
            List<StepMessageEntity> messages = baseMapper.selectByScenarioId(scenarioId);
            log.info("获取到消息数量: {}", messages != null ? messages.size() : 0);
            return messages;
        } catch (Exception e) {
            log.error("获取场景消息失败，场景ID: {}", scenarioId, e);
            return null;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean batchSaveMessages(String stepId, List<StepMessageEntity> messages) {
        try {
            log.info("批量保存步骤消息，步骤ID: {}, 消息数量: {}", stepId, messages != null ? messages.size() : 0);
            
            // 先删除原有消息
            int deletedCount = baseMapper.deleteByStepId(stepId);
            log.info("删除原有消息数量: {}", deletedCount);
            
            // 批量保存新消息
            if (messages != null && !messages.isEmpty()) {
                for (int i = 0; i < messages.size(); i++) {
                    StepMessageEntity message = messages.get(i);
                    message.setStepId(stepId);
                    message.setMessageOrder(i + 1);
                    
                    // 生成消息ID
                    if (message.getMessageId() == null || message.getMessageId().trim().isEmpty()) {
                        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
                        String uuid = UUID.randomUUID().toString().substring(0, 8);
                        message.setMessageId("MSG_" + timestamp + "_" + uuid);
                    }
                    
                    // 设置默认值
                    if (message.getSpeechRate() == null) {
                        message.setSpeechRate(new java.math.BigDecimal("1.0"));
                    }
                    if (message.getWaitTimeSeconds() == null) {
                        message.setWaitTimeSeconds(3);
                    }
                    if (message.getIsActive() == null) {
                        message.setIsActive(1);
                    }
                    if (message.getMessageType() == null) {
                        message.setMessageType("normal");
                    }
                    
                    save(message);
                }
                log.info("批量保存步骤消息成功");
            }
            
            return true;
        } catch (Exception e) {
            log.error("批量保存步骤消息失败，步骤ID: {}", stepId, e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int deleteMessagesByStepId(String stepId) {
        try {
            log.info("删除步骤消息，步骤ID: {}", stepId);
            int count = baseMapper.deleteByStepId(stepId);
            log.info("删除消息数量: {}", count);
            return count;
        } catch (Exception e) {
            log.error("删除步骤消息失败，步骤ID: {}", stepId, e);
            return 0;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int deleteMessagesByScenarioId(String scenarioId) {
        try {
            log.info("删除场景消息，场景ID: {}", scenarioId);
            int count = baseMapper.deleteByScenarioId(scenarioId);
            log.info("删除消息数量: {}", count);
            return count;
        }
        catch (Exception e) {
            log.error("删除场景消息失败，场景ID: {}", scenarioId, e);
            return 0;
        }
    }

    @Override
    public int countMessagesByStepId(String stepId) {
        try {
            int count = baseMapper.countByStepId(stepId);
            log.debug("步骤消息数量，步骤ID: {}, 数量: {}", stepId, count);
            return count;
        } catch (Exception e) {
            log.error("统计步骤消息数量失败，步骤ID: {}", stepId, e);
            return 0;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean reorderMessages(String stepId, List<StepMessageEntity> messageOrders) {
        try {
            log.info("重新排序步骤消息，步骤ID: {}, 消息数量: {}", stepId, messageOrders != null ? messageOrders.size() : 0);
            
            if (messageOrders != null && !messageOrders.isEmpty()) {
                for (int i = 0; i < messageOrders.size(); i++) {
                    StepMessageEntity message = messageOrders.get(i);
                    message.setMessageOrder(i + 1);
                    updateById(message);
                }
                log.info("重新排序步骤消息成功");
            }
            
            return true;
        } catch (Exception e) {
            log.error("重新排序步骤消息失败，步骤ID: {}", stepId, e);
            return false;
        }
    }
}
