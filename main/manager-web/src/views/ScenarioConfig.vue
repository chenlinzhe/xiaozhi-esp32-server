<template>
  <div class="scenario-config">
    <HeaderBar />
    
    <div class="operation-bar">
      <h2 class="page-title">场景配置</h2>
      <div class="right-operations">
        <el-button type="primary" @click="createScenario">新建场景</el-button>
        <el-button @click="importTemplate">导入模板</el-button>
      </div>
    </div>
    
    <div class="main-wrapper">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="场景名称">
            <el-input v-model="searchForm.scenarioName" placeholder="请输入场景名称" clearable />
          </el-form-item>
          <el-form-item label="场景类型">
            <el-select v-model="searchForm.scenarioType" placeholder="请选择场景类型" clearable>
              <el-option label="表达需求" value="express_needs" />
              <el-option label="问候语" value="greeting" />
              <el-option label="情感表达" value="emotion" />
              <el-option label="社交技能" value="social" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="searchForm.isActive" placeholder="请选择状态" clearable>
              <el-option label="启用" :value="1" />
              <el-option label="禁用" :value="0" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="searchScenarios">搜索</el-button>
            <el-button @click="resetSearch">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 场景列表 -->
      <div class="scenario-list">
        <el-row :gutter="20">
          <el-col :span="8" v-for="scenario in scenarios" :key="scenario.id">
            <el-card class="scenario-card" shadow="hover">
              <div class="scenario-header">
                <h3 class="scenario-title">{{ scenario.scenarioName }}</h3>
                <div class="scenario-actions">
                  <el-button size="mini" type="primary" @click="editScenario(scenario)">编辑</el-button>
                  <el-button size="mini" @click="configureSteps(scenario)">配置步骤</el-button>
                  <el-button size="mini" type="success" @click="testScenario(scenario)">测试</el-button>
                  <el-switch 
                    v-model="scenario.isActive" 
                    @change="toggleScenario(scenario)"
                    active-color="#13ce66"
                    inactive-color="#ff4949" />
                </div>
              </div>
              
              <div class="scenario-info">
                <el-tag :type="getScenarioTypeColor(scenario.scenarioType)" size="small">
                  {{ getScenarioTypeLabel(scenario.scenarioType) }}
                </el-tag>
                <span class="difficulty">难度: {{ scenario.difficultyLevel }}</span>
                <span class="target-age">年龄: {{ scenario.targetAge }}</span>
                <span class="step-count">步骤数: {{ scenario.stepCount || 0 }}</span>
              </div>
              
              <div class="scenario-description">
                <p>{{ scenario.description || '暂无描述' }}</p>
              </div>
              
              <div class="scenario-footer">
                <span class="trigger-type">触发方式: {{ getTriggerTypeLabel(scenario.triggerType) }}</span>
                <span class="create-time">创建时间: {{ formatDate(scenario.createdAt) }}</span>
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 分页 -->
        <div class="pagination-wrapper" v-if="total > 0">
          <el-pagination
            @current-change="handleCurrentChange"
            @size-change="handleSizeChange"
            :current-page="currentPage"
            :page-sizes="[10, 20, 50, 100]"
            :page-size="pageSize"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total">
          </el-pagination>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Api from '@/apis/api';
import HeaderBar from '@/components/HeaderBar.vue';

export default {
  name: 'ScenarioConfig',
  components: { HeaderBar },
  data() {
    return {
      scenarios: [],
      loading: false,
      searchForm: {
        scenarioName: '',
        scenarioType: '',
        isActive: ''
      },
      currentPage: 1,
      pageSize: 10,
      total: 0
    }
  },
  mounted() {
    this.fetchScenarioList();
  },
  methods: {
    async fetchScenarioList() {
      try {
        this.loading = true;
        const params = {
          page: this.currentPage,
          limit: this.pageSize,
          ...this.searchForm
        };
        
        const response = await Api.getScenarioList(params);
        this.scenarios = response.data.list;
        this.total = response.data.total;
      } catch (error) {
        this.$message.error('获取场景列表失败');
        console.error('获取场景列表失败:', error);
      } finally {
        this.loading = false;
      }
    },
    
    searchScenarios() {
      this.currentPage = 1;
      this.fetchScenarioList();
    },
    
    resetSearch() {
      this.searchForm = {
        scenarioName: '',
        scenarioType: '',
        isActive: ''
      };
      this.currentPage = 1;
      this.fetchScenarioList();
    },
    
    handleCurrentChange(page) {
      this.currentPage = page;
      this.fetchScenarioList();
    },
    
    handleSizeChange(size) {
      this.pageSize = size;
      this.currentPage = 1;
      this.fetchScenarioList();
    },
    
    createScenario() {
      this.$router.push('/scenario-create');
    },
    
    editScenario(scenario) {
      this.$router.push(`/scenario-edit/${scenario.id}`);
    },
    
    configureSteps(scenario) {
      this.$router.push(`/scenario-steps/${scenario.id}`);
    },
    
    testScenario(scenario) {
      this.$message.info('测试功能开发中...');
    },
    
    async toggleScenario(scenario) {
      try {
        await Api.toggleScenario(scenario.id, scenario.isActive);
        this.$message.success('场景状态更新成功');
      } catch (error) {
        this.$message.error('更新失败');
        scenario.isActive = !scenario.isActive; // 恢复状态
      }
    },
    
    importTemplate() {
      this.$message.info('导入模板功能开发中...');
    },
    
    getScenarioTypeColor(type) {
      const colorMap = {
        'express_needs': 'primary',
        'greeting': 'success',
        'emotion': 'warning',
        'social': 'info'
      };
      return colorMap[type] || 'default';
    },
    
    getScenarioTypeLabel(type) {
      const labelMap = {
        'express_needs': '表达需求',
        'greeting': '问候语',
        'emotion': '情感表达',
        'social': '社交技能'
      };
      return labelMap[type] || type;
    },
    
    getTriggerTypeLabel(type) {
      const labelMap = {
        'voice': '语音触发',
        'visual': '视觉触发',
        'button': '按钮触发'
      };
      return labelMap[type] || type;
    },
    
    formatDate(date) {
      if (!date) return '';
      return new Date(date).toLocaleDateString();
    }
  }
}
</script>

<style scoped>
.scenario-config {
  padding: 20px;
}

.operation-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  color: #303133;
}

.search-bar {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.search-form {
  margin: 0;
}

.scenario-list {
  margin-top: 20px;
}

.scenario-card {
  margin-bottom: 20px;
  transition: all 0.3s;
}

.scenario-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.scenario-title {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.scenario-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.scenario-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.scenario-info span {
  font-size: 12px;
  color: #606266;
}

.scenario-description {
  margin-bottom: 10px;
}

.scenario-description p {
  margin: 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.scenario-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.pagination-wrapper {
  text-align: center;
  margin-top: 20px;
}
</style> 