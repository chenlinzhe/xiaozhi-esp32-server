package xiaozhi.modules.scenario.service;

import com.baomidou.mybatisplus.extension.service.IService;
import xiaozhi.common.page.PageData;
import xiaozhi.modules.scenario.entity.ChildLearningRecordEntity;

import java.util.List;
import java.util.Map;

/**
 * 儿童学习记录Service接口
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
public interface ChildLearningRecordService extends IService<ChildLearningRecordEntity> {

    /**
     * 分页查询学习记录
     * 
     * @param params 查询参数
     * @return 分页数据
     */
    PageData<ChildLearningRecordEntity> page(Map<String, Object> params);

    /**
     * 根据智能体ID获取学习记录
     * 
     * @param agentId 智能体ID
     * @return 学习记录列表
     */
    List<ChildLearningRecordEntity> getByAgentId(String agentId);

    /**
     * 根据场景ID获取学习记录
     * 
     * @param scenarioId 场景ID
     * @return 学习记录列表
     */
    List<ChildLearningRecordEntity> getByScenarioId(String scenarioId);

    /**
     * 根据儿童姓名获取学习记录
     * 
     * @param childName 儿童姓名
     * @return 学习记录列表
     */
    List<ChildLearningRecordEntity> getByChildName(String childName);

    /**
     * 获取学习统计信息
     * 
     * @param agentId 智能体ID
     * @param childName 儿童姓名
     * @return 统计信息
     */
    ChildLearningRecordEntity getStatistics(String agentId, String childName);

    /**
     * 保存学习记录
     * 
     * @param entity 学习记录实体
     * @return 是否成功
     */
    boolean saveLearningRecord(ChildLearningRecordEntity entity);

    /**
     * 更新学习记录
     * 
     * @param entity 学习记录实体
     * @return 是否成功
     */
    boolean updateLearningRecord(ChildLearningRecordEntity entity);
}
