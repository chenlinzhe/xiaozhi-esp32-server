<template>
  <div class="learning-record-management">
    <HeaderBar />
    
    <div class="operation-bar">
      <h2 class="page-title">学习记录管理</h2>
      <div class="right-operations">
        <el-button @click="exportRecords">导出记录</el-button>
        <el-button type="primary" @click="generateReport">生成报告</el-button>
      </div>
    </div>
    
    <div class="main-wrapper">
      <!-- 统计卡片 -->
      <div class="statistics-cards">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ statistics.totalRecords }}</div>
                <div class="stat-label">总学习记录</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ statistics.avgSuccessRate }}%</div>
                <div class="stat-label">平均成功率</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ statistics.totalDuration }}</div>
                <div class="stat-label">总学习时长(分钟)</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ statistics.activeChildren }}</div>
                <div class="stat-label">活跃儿童数</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="儿童姓名">
            <el-input v-model="searchForm.childName" placeholder="请输入儿童姓名" clearable />
          </el-form-item>
          <el-form-item label="场景名称">
            <el-input v-model="searchForm.scenarioName" placeholder="请输入场景名称" clearable />
          </el-form-item>
          <el-form-item label="智能体">
            <el-select v-model="searchForm.agentId" placeholder="请选择智能体" clearable>
              <el-option 
                v-for="agent in agents" 
                :key="agent.id" 
                :label="agent.agentName" 
                :value="agent.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="searchForm.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="yyyy-MM-dd"
              value-format="yyyy-MM-dd">
            </el-date-picker>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="searchRecords">搜索</el-button>
            <el-button @click="resetSearch">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- 记录列表 -->
      <div class="record-list">
        <el-table :data="records" v-loading="loading" stripe>
          <el-table-column prop="childName" label="儿童姓名" width="120" />
          <el-table-column prop="scenarioName" label="场景名称" width="200" />
          <el-table-column prop="agentName" label="智能体" width="150" />
          <el-table-column prop="startTime" label="开始时间" width="180">
            <template slot-scope="scope">
              {{ formatDateTime(scope.row.startTime) }}
            </template>
          </el-table-column>
          <el-table-column prop="endTime" label="结束时间" width="180">
            <template slot-scope="scope">
              {{ formatDateTime(scope.row.endTime) }}
            </template>
          </el-table-column>
          <el-table-column prop="learningDurationFormatted" label="学习时长" width="120" />
          <el-table-column prop="completedSteps" label="完成步骤" width="100">
            <template slot-scope="scope">
              {{ scope.row.completedSteps }}/{{ scope.row.totalSteps }}
            </template>
          </el-table-column>
          <el-table-column prop="successRate" label="成功率" width="100">
            <template slot-scope="scope">
              <el-progress 
                :percentage="scope.row.successRate" 
                :color="getProgressColor(scope.row.successRate)"
                :stroke-width="8">
              </el-progress>
            </template>
          </el-table-column>
          <el-table-column prop="difficultyRating" label="难度评分" width="100">
            <template slot-scope="scope">
              <el-rate 
                v-model="scope.row.difficultyRating" 
                disabled 
                show-score 
                text-color="#ff9900">
              </el-rate>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template slot-scope="scope">
              <el-button size="mini" @click="viewDetail(scope.row)">详情</el-button>
              <el-button size="mini" type="danger" @click="deleteRecord(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        
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
      
      <!-- 详情对话框 -->
      <el-dialog title="学习记录详情" :visible.sync="detailDialogVisible" width="60%">
        <div v-if="currentRecord" class="record-detail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="儿童姓名">{{ currentRecord.childName }}</el-descriptions-item>
            <el-descriptions-item label="场景名称">{{ currentRecord.scenarioName }}</el-descriptions-item>
            <el-descriptions-item label="智能体">{{ currentRecord.agentName }}</el-descriptions-item>
            <el-descriptions-item label="学习时长">{{ currentRecord.learningDurationFormatted }}</el-descriptions-item>
            <el-descriptions-item label="完成步骤">{{ currentRecord.completedSteps }}/{{ currentRecord.totalSteps }}</el-descriptions-item>
            <el-descriptions-item label="成功率">{{ currentRecord.successRate }}%</el-descriptions-item>
            <el-descriptions-item label="开始时间">{{ formatDateTime(currentRecord.startTime) }}</el-descriptions-item>
            <el-descriptions-item label="结束时间">{{ formatDateTime(currentRecord.endTime) }}</el-descriptions-item>
            <el-descriptions-item label="难度评分">
              <el-rate v-model="currentRecord.difficultyRating" disabled show-score></el-rate>
            </el-descriptions-item>
            <el-descriptions-item label="学习笔记" :span="2">
              {{ currentRecord.notes || '暂无笔记' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script>
import Api from '@/apis/module/scenario';
import { isApiSuccess, getBusinessData, getErrorMessage, ApiLogger } from '@/utils/apiHelper';
import HeaderBar from '@/components/HeaderBar.vue';

export default {
  name: 'LearningRecordManagement',
  components: { HeaderBar },
  data() {
    return {
      records: [],
      agents: [],
      loading: false,
      searchForm: {
        childName: '',
        scenarioName: '',
        agentId: '',
        dateRange: []
      },
      currentPage: 1,
      pageSize: 10,
      total: 0,
      statistics: {
        totalRecords: 0,
        avgSuccessRate: 0,
        totalDuration: 0,
        activeChildren: 0
      },
      detailDialogVisible: false,
      currentRecord: null
    }
  },
  mounted() {
    this.loadRecords();
    this.loadAgents();
    this.loadStatistics();
  },
  methods: {
    loadRecords() {
      this.loading = true;
      const params = {
        page: this.currentPage,
        limit: this.pageSize,
        ...this.searchForm
      };
      
      Api.getLearningRecords(params, (data) => {
        this.loading = false;
        ApiLogger.log('学习记录响应数据:', data);
        
        if (isApiSuccess(data)) {
          const businessData = getBusinessData(data);
          if (businessData && businessData.list) {
            this.records = businessData.list;
            this.total = businessData.total || 0;
            ApiLogger.log('学习记录数据设置成功:', this.records);
          } else if (businessData && Array.isArray(businessData)) {
            // 如果businessData直接是数组，说明没有分页结构
            this.records = businessData;
            this.total = businessData.length;
            ApiLogger.log('学习记录数据设置成功（数组格式）:', this.records);
          } else {
            ApiLogger.error('响应数据格式不正确，缺少list字段');
            this.records = [];
            this.total = 0;
            this.$message.error('响应数据格式不正确');
          }
        } else {
          const errorMsg = getErrorMessage(data, '获取学习记录失败');
          ApiLogger.error('学习记录请求失败:', errorMsg);
          this.records = [];
          this.total = 0;
          this.$message.error(errorMsg);
        }
      });
    },
    
    loadAgents() {
      // 这里需要根据实际的智能体API来调用
      // 暂时使用模拟数据
      this.agents = [
        { id: 'agent_001', agentName: '智能体1' },
        { id: 'agent_002', agentName: '智能体2' },
        { id: 'agent_003', agentName: '智能体3' }
      ];
    },
    
    loadStatistics() {
      try {
        // 这里可以调用统计API，暂时使用模拟数据
        this.statistics = {
          totalRecords: this.total,
          avgSuccessRate: 85.6,
          totalDuration: 1200,
          activeChildren: 12
        };
      } catch (error) {
        ApiLogger.error('获取统计数据失败:', error);
      }
    },
    
    searchRecords() {
      this.currentPage = 1;
      this.loadRecords();
    },
    
    resetSearch() {
      this.searchForm = {
        childName: '',
        scenarioName: '',
        agentId: '',
        dateRange: []
      };
      this.currentPage = 1;
      this.loadRecords();
    },
    
    handleCurrentChange(page) {
      this.currentPage = page;
      this.loadRecords();
    },
    
    handleSizeChange(size) {
      this.pageSize = size;
      this.currentPage = 1;
      this.loadRecords();
    },
    
    viewDetail(record) {
      this.currentRecord = record;
      this.detailDialogVisible = true;
    },
    
    deleteRecord(record) {
      this.$confirm('确定要删除这条学习记录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        Api.deleteLearningRecord(record.id, (data) => {
          ApiLogger.log('删除学习记录响应:', data);
          
          if (isApiSuccess(data)) {
            this.$message.success('删除成功');
            this.loadRecords();
          } else {
            const errorMsg = getErrorMessage(data, '删除失败');
            this.$message.error(errorMsg);
            ApiLogger.error('删除学习记录失败:', errorMsg);
          }
        });
      }).catch(() => {
        // 用户取消删除
      });
    },
    
    exportRecords() {
      this.$message.info('导出功能开发中...');
    },
    
    generateReport() {
      this.$message.info('报告生成功能开发中...');
    },
    
    formatDateTime(dateTime) {
      if (!dateTime) return '';
      return new Date(dateTime).toLocaleString();
    },
    
    getProgressColor(percentage) {
      if (percentage >= 80) return '#67C23A';
      if (percentage >= 60) return '#E6A23C';
      return '#F56C6C';
    }
  }
}
</script>

<style scoped>
.learning-record-management {
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

.main-wrapper {
  max-width: 1400px;
  margin: 0 auto;
}

.statistics-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
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

.record-list {
  margin-top: 20px;
}

.pagination-wrapper {
  text-align: center;
  margin-top: 20px;
}

.record-detail {
  padding: 20px 0;
}
</style>
