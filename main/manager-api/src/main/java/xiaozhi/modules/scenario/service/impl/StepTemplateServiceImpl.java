package xiaozhi.modules.scenario.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import xiaozhi.modules.scenario.dao.StepTemplateMapper;
import xiaozhi.modules.scenario.entity.StepTemplateEntity;
import xiaozhi.modules.scenario.service.StepTemplateService;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.UUID;

/**
 * 步骤模板Service实现类
 * 
 * @author xiaozhi
 * @since 2024-12-01
 */
@Service
public class StepTemplateServiceImpl extends ServiceImpl<StepTemplateMapper, StepTemplateEntity> implements StepTemplateService {

    @Override
    public List<StepTemplateEntity> getByType(String templateType) {
        return baseMapper.selectByType(templateType);
    }

    @Override
    public List<StepTemplateEntity> getDefaultTemplates() {
        return baseMapper.selectDefaultTemplates();
    }

    @Override
    public StepTemplateEntity getDefaultByType(String templateType) {
        return baseMapper.selectDefaultByType(templateType);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean saveTemplate(StepTemplateEntity entity) {
        // 生成唯一的模板ID
        if (entity.getTemplateId() == null || entity.getTemplateId().trim().isEmpty()) {
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            String uuid = UUID.randomUUID().toString().substring(0, 8);
            entity.setTemplateId("TEMPLATE_" + timestamp + "_" + uuid);
        }
        
        // 设置默认值
        if (entity.getIsDefault() == null) {
            entity.setIsDefault(0);
        }
        if (entity.getSortOrder() == null) {
            entity.setSortOrder(0);
        }
        
        return save(entity);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateTemplate(StepTemplateEntity entity) {
        return updateById(entity);
    }
}
