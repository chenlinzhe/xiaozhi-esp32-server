package xiaozhi.modules.scenario.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.modules.scenario.dao.ChildLearningRecordMapper;
import xiaozhi.modules.scenario.entity.ChildLearningRecordEntity;
import xiaozhi.modules.scenario.service.ChildLearningRecordService;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 儿童学习记录Service实现类
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Service
public class ChildLearningRecordServiceImpl extends ServiceImpl<ChildLearningRecordMapper, ChildLearningRecordEntity> implements ChildLearningRecordService {

    @Override
    public PageData<ChildLearningRecordEntity> page(Map<String, Object> params) {
        // 构建查询条件
        QueryWrapper<ChildLearningRecordEntity> queryWrapper = new QueryWrapper<>();
        
        // 根据智能体ID查询
        if (params.get("agentId") != null) {
            queryWrapper.eq("agent_id", params.get("agentId"));
        }
        
        // 根据场景ID查询
        if (params.get("scenarioId") != null) {
            queryWrapper.eq("scenario_id", params.get("scenarioId"));
        }
        
        // 根据儿童姓名查询
        if (params.get("childName") != null) {
            queryWrapper.like("child_name", params.get("childName"));
        }
        
        // 排序
        queryWrapper.orderByDesc("created_at");
        
        // 分页查询
        return getPage(params, queryWrapper);
    }

    @Override
    public List<ChildLearningRecordEntity> getByAgentId(String agentId) {
        return baseMapper.selectByAgentId(agentId);
    }

    @Override
    public List<ChildLearningRecordEntity> getByScenarioId(String scenarioId) {
        return baseMapper.selectByScenarioId(scenarioId);
    }

    @Override
    public List<ChildLearningRecordEntity> getByChildName(String childName) {
        return baseMapper.selectByChildName(childName);
    }

    @Override
    public ChildLearningRecordEntity getStatistics(String agentId, String childName) {
        return baseMapper.selectStatistics(agentId, childName);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean saveLearningRecord(ChildLearningRecordEntity entity) {
        // 生成唯一的记录ID
        if (entity.getRecordId() == null || entity.getRecordId().trim().isEmpty()) {
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            String uuid = UUID.randomUUID().toString().substring(0, 8);
            entity.setRecordId("RECORD_" + timestamp + "_" + uuid);
        }
        
        return save(entity);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateLearningRecord(ChildLearningRecordEntity entity) {
        return updateById(entity);
    }

    /**
     * 分页查询
     */
    private PageData<ChildLearningRecordEntity> getPage(Map<String, Object> params, QueryWrapper<ChildLearningRecordEntity> queryWrapper) {
        // 获取分页参数
        int page = ConvertUtils.intValue(params.get("page"), 1);
        int limit = ConvertUtils.intValue(params.get("limit"), 10);
        
        // 计算偏移量
        int offset = (page - 1) * limit;
        
        // 查询总数
        long total = count(queryWrapper);
        
        // 查询数据
        queryWrapper.last("LIMIT " + offset + "," + limit);
        List<ChildLearningRecordEntity> list = list(queryWrapper);
        
        // 构建分页数据
        return new PageData<>(list, total);
    }
}
