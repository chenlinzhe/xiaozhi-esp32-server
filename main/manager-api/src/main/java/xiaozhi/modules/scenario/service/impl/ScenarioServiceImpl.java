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
        // 构建查询条件
        QueryWrapper<ScenarioEntity> queryWrapper = new QueryWrapper<>();
        
        // 根据智能体ID查询
        if (params.get("agentId") != null) {
            queryWrapper.eq("agent_id", params.get("agentId"));
        }
        
        // 根据场景类型查询
        if (params.get("scenarioType") != null) {
            queryWrapper.eq("scenario_type", params.get("scenarioType"));
        }
        
        // 根据启用状态查询
        if (params.get("isActive") != null) {
            queryWrapper.eq("is_active", params.get("isActive"));
        }
        
        // 根据场景名称模糊查询
        if (params.get("scenarioName") != null) {
            queryWrapper.like("scenario_name", params.get("scenarioName"));
        }
        
        // 排序
        queryWrapper.orderByAsc("sort_order").orderByDesc("created_at");
        
        // 分页查询
        return getPage(params, queryWrapper);
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
        return removeById(id);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean toggleScenario(String id, Integer isActive) {
        ScenarioEntity entity = new ScenarioEntity();
        entity.setId(id);
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
        PageData<ScenarioEntity> pageData = new PageData<>();
        pageData.setList(list);
        pageData.setTotal(total);
        pageData.setPage(page);
        pageData.setLimit(limit);
        
        return pageData;
    }
} 