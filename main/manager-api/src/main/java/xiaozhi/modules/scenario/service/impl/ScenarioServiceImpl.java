package xiaozhi.modules.scenario.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.modules.scenario.dao.ScenarioMapper;
import xiaozhi.modules.scenario.entity.ScenarioEntity;
import xiaozhi.modules.scenario.service.ScenarioService;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

import java.util.List;
import java.util.Map;

/**
 * 场景配置Service实现类
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Service
public class ScenarioServiceImpl extends ServiceImpl<ScenarioMapper, ScenarioEntity> implements ScenarioService {

    @Override
    public PageData<ScenarioEntity> page(Map<String, Object> params) {
        // 获取分页参数
        int page = ConvertUtils.intValue(params.get("page"), 1);
        int limit = ConvertUtils.intValue(params.get("limit"), 10);
        
        // 过滤空字符串参数
        if (params.get("isActive") != null && "".equals(params.get("isActive"))) {
            params.remove("isActive");
        }
        if (params.get("scenarioType") != null && "".equals(params.get("scenarioType"))) {
            params.remove("scenarioType");
        }
        if (params.get("scenarioName") != null && "".equals(params.get("scenarioName"))) {
            params.remove("scenarioName");
        }
        if (params.get("agentId") != null && "".equals(params.get("agentId"))) {
            params.remove("agentId");
        }
        
        // 计算偏移量
        int offset = (page - 1) * limit;
        
        // 添加分页参数
        params.put("offset", offset);
        params.put("limit", limit);
        
        // 查询总数
        long total = baseMapper.selectScenarioListCount(params);
        
        // 使用自定义查询获取数据（包含步骤数量和智能体名称）
        List<ScenarioEntity> list = baseMapper.selectScenarioList(params);
        
        // 构建分页数据
        return new PageData<>(list, total);
    }

    @Override
    public List<ScenarioEntity> getByAgentId(String agentId) {
        return baseMapper.selectByAgentId(agentId);
    }

    @Override
    public List<ScenarioEntity> getActiveByType(String scenarioType) {
        return baseMapper.selectByTypeAndStatus(scenarioType, 1);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean saveScenario(ScenarioEntity entity) {
        // 生成唯一的场景ID
        if (entity.getScenarioId() == null || entity.getScenarioId().trim().isEmpty()) {
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            String uuid = UUID.randomUUID().toString().substring(0, 8);
            entity.setScenarioId("SCENARIO_" + timestamp + "_" + uuid);
        }
        
        // 设置默认值
        if (entity.getIsActive() == null) {
            entity.setIsActive(1);
        }
        if (entity.getDifficultyLevel() == null) {
            entity.setDifficultyLevel(1);
        }
        if (entity.getSortOrder() == null) {
            entity.setSortOrder(0);
        }
        
        return save(entity);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateScenario(ScenarioEntity entity) {
        return updateById(entity);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteScenario(String id) {
        return removeById(Long.valueOf(id));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean toggleScenario(String id, Integer isActive) {
        ScenarioEntity entity = new ScenarioEntity();
        entity.setId(Long.valueOf(id));
        entity.setIsActive(isActive);
        return updateById(entity);
    }

    /**
     * 分页查询
     */
    private PageData<ScenarioEntity> getPage(Map<String, Object> params, QueryWrapper<ScenarioEntity> queryWrapper) {
        // 获取分页参数
        int page = ConvertUtils.intValue(params.get("page"), 1);
        int limit = ConvertUtils.intValue(params.get("limit"), 10);
        
        // 计算偏移量
        int offset = (page - 1) * limit;
        
        // 查询总数
        long total = count(queryWrapper);
        
        // 查询数据
        queryWrapper.last("LIMIT " + offset + "," + limit);
        List<ScenarioEntity> list = list(queryWrapper);
        
        // 构建分页数据
        return new PageData<>(list, total);
    }
} 