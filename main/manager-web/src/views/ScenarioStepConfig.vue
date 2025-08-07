<template>
  <div class="scenario-step-config">
    <HeaderBar />
    
    <div class="operation-bar">
      <h2 class="page-title">对话步骤配置 - {{ scenario.scenarioName }}</h2>
      <div class="right-operations">
        <el-button type="primary" @click="addStep">添加步骤</el-button>
        <el-button @click="importStepTemplate">导入步骤模板</el-button>
        <el-button @click="saveSteps">保存配置</el-button>
        <el-button @click="goBack">返回</el-button>
      </div>
    </div>
    
    <div class="main-wrapper">
      <!-- 场景信息 -->
      <el-card class="scenario-info-card" v-if="scenario.id">
        <div class="scenario-info">
          <div class="info-item">
            <span class="label">场景名称：</span>
            <span class="value">{{ scenario.scenarioName }}</span>
          </div>
          <div class="info-item">
            <span class="label">场景类型：</span>
            <span class="value">{{ getScenarioTypeLabel(scenario.scenarioType) }}</span>
          </div>
          <div class="info-item">
            <span class="label">触发方式：</span>
            <span class="value">{{ getTriggerTypeLabel(scenario.triggerType) }}</span>
          </div>
          <div class="info-item">
            <span class="label">难度等级：</span>
            <span class="value">{{ scenario.difficultyLevel }}</span>
          </div>
        </div>
      </el-card>
      
      <!-- 步骤列表 -->
      <div class="step-list">
        <el-card v-for="(step, index) in steps" :key="step.id" class="step-card">
          <div class="step-header">
            <div class="step-info">
              <span class="step-number">步骤 {{ index + 1 }}</span>
              <el-input 
                v-model="step.stepName" 
                placeholder="步骤名称"
                size="small"
                class="step-name-input" />
              <el-tag :type="getStepTypeColor(step.stepType)" size="small">
                {{ getStepTypeLabel(step.stepType) }}
              </el-tag>
            </div>
            <div class="step-actions">
              <el-button size="mini" @click="moveStep(index, -1)" :disabled="index === 0">
                <i class="el-icon-arrow-up"></i>
              </el-button>
              <el-button size="mini" @click="moveStep(index, 1)" :disabled="index === steps.length - 1">
                <i class="el-icon-arrow-down"></i>
              </el-button>
              <el-button size="mini" type="danger" @click="removeStep(index)">
                <i class="el-icon-delete"></i>
              </el-button>
            </div>
          </div>
          
          <div class="step-content">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="AI消息" class="form-item">
                  <el-input 
                    type="textarea" 
                    v-model="step.aiMessage" 
                    :rows="3"
                    placeholder="请输入AI要说的内容，支持使用 **{childName}** 替换儿童姓名" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="期望关键词" class="form-item">
                  <el-input 
                    type="textarea" 
                    v-model="step.expectedKeywords" 
                    :rows="3"
                    placeholder="请输入期望的关键词，JSON格式，如：['你好', 'hi']" />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="期望短语" class="form-item">
                  <el-input 
                    type="textarea" 
                    v-model="step.expectedPhrases" 
                    :rows="3"
                    placeholder="请输入期望的短语，JSON格式，如：['你好', 'hi']" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="成功条件" class="form-item">
                  <el-select v-model="step.successCondition" placeholder="请选择成功条件">
                    <el-option label="完全匹配" value="exact" />
                    <el-option label="部分匹配" value="partial" />
                    <el-option label="关键词匹配" value="keyword" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="最大尝试次数" class="form-item">
                  <el-input-number 
                    v-model="step.maxAttempts" 
                    :min="1" 
                    :max="10"
                    size="small" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="超时时间(秒)" class="form-item">
                  <el-input-number 
                    v-model="step.timeoutSeconds" 
                    :min="5" 
                    :max="60"
                    size="small" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="步骤类型" class="form-item">
                  <el-select v-model="step.stepType" placeholder="请选择步骤类型">
                    <el-option label="普通步骤" value="normal" />
                    <el-option label="可选步骤" value="optional" />
                    <el-option label="分支步骤" value="branch" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="替代消息" class="form-item">
                  <el-input 
                    type="textarea" 
                    v-model="step.alternativeMessage" 
                    :rows="2"
                    placeholder="当用户回答错误时的提示消息" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="手势提示" class="form-item">
                  <el-input 
                    v-model="step.gestureHint" 
                    placeholder="如：指嘴巴、指肚子、指眼睛等" />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="音效文件" class="form-item">
                  <el-input 
                    v-model="step.musicEffect" 
                    placeholder="音效文件路径，如：/audio/success.mp3" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="下一步骤ID" class="form-item">
                  <el-input 
                    v-model="step.nextStepId" 
                    placeholder="指定下一步骤ID，留空则按顺序执行" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </div>
      
      <!-- 空状态 -->
      <div v-if="steps.length === 0" class="empty-state">
        <el-empty description="暂无步骤配置">
          <el-button type="primary" @click="addStep">添加第一个步骤</el-button>
        </el-empty>
      </div>
      
      <!-- 模板选择对话框 -->
      <el-dialog title="选择步骤模板" :visible.sync="templateDialogVisible" width="60%">
        <div class="template-list">
          <el-table :data="stepTemplates" @row-click="selectTemplate">
            <el-table-column prop="templateName" label="模板名称" />
            <el-table-column prop="templateType" label="模板类型" />
            <el-table-column prop="description" label="描述" />
            <el-table-column label="操作" width="100">
              <template slot-scope="scope">
                <el-button size="mini" type="primary" @click="selectTemplate(scope.row)">
                  选择
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script>
import Api from '@/apis/api';
import HeaderBar from '@/components/HeaderBar.vue';

export default {
  name: 'ScenarioStepConfig',
  components: { HeaderBar },
  data() {
    return {
      scenarioId: '',
      scenario: {},
      steps: [],
      stepTemplates: [],
      templateDialogVisible: false,
      loading: false
    }
  },
  mounted() {
    this.scenarioId = this.$route.params.id;
    this.loadScenarioData();
    this.loadStepTemplates();
  },
  methods: {
    async loadScenarioData() {
      try {
        this.loading = true;
        const [scenarioRes, stepsRes] = await Promise.all([
          this.getScenarioData(),
          this.getScenarioStepsData()
        ]);
        this.scenario = scenarioRes.data;
        this.steps = stepsRes.data || [];
      } catch (error) {
        this.$message.error('加载场景数据失败');
        console.error('加载场景数据失败:', error);
      } finally {
        this.loading = false;
      }
    },
    
    getScenarioData() {
      return new Promise((resolve, reject) => {
        Api.scenario.getScenario(this.scenarioId, (res) => {
          if (res.code === 0) {
            resolve(res);
          } else {
            reject(new Error(res.msg));
          }
        });
      });
    },
    
    getScenarioStepsData() {
      return new Promise((resolve, reject) => {
        Api.scenario.getScenarioSteps(this.scenarioId, (res) => {
          if (res.code === 0) {
            resolve(res);
          } else {
            reject(new Error(res.msg));
          }
        });
      });
    },
    
    async loadStepTemplates() {
      try {
        Api.scenario.getStepTemplateList((res) => {
          if (res.code === 0) {
            this.stepTemplates = res.data || [];
          }
        });
      } catch (error) {
        console.error('加载步骤模板失败:', error);
      }
    },
    
    addStep() {
      const newStep = {
        id: this.generateId(),
        stepName: `步骤${this.steps.length + 1}`,
        aiMessage: '',
        expectedKeywords: '[]',
        expectedPhrases: '[]',
        successCondition: 'partial',
        maxAttempts: 3,
        timeoutSeconds: 10,
        alternativeMessage: '',
        gestureHint: '',
        musicEffect: '',
        stepType: 'normal',
        stepOrder: this.steps.length + 1,
        nextStepId: '',
        retryStepId: ''
      };
      this.steps.push(newStep);
    },
    
    removeStep(index) {
      this.$confirm('确定要删除这个步骤吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.steps.splice(index, 1);
        this.updateStepOrder();
      }).catch(() => {});
    },
    
    moveStep(index, direction) {
      const newIndex = index + direction;
      if (newIndex >= 0 && newIndex < this.steps.length) {
        const temp = this.steps[index];
        this.steps[index] = this.steps[newIndex];
        this.steps[newIndex] = temp;
        this.updateStepOrder();
      }
    },
    
    updateStepOrder() {
      this.steps.forEach((step, index) => {
        step.stepOrder = index + 1;
      });
    },
    
    async saveSteps() {
      try {
        // 验证步骤数据
        for (let i = 0; i < this.steps.length; i++) {
          const step = this.steps[i];
          if (!step.stepName.trim()) {
            this.$message.error(`步骤${i + 1}的名称不能为空`);
            return;
          }
          if (!step.aiMessage.trim()) {
            this.$message.error(`步骤${i + 1}的AI消息不能为空`);
            return;
          }
          
          // 验证JSON格式
          try {
            if (step.expectedKeywords) {
              JSON.parse(step.expectedKeywords);
            }
            if (step.expectedPhrases) {
              JSON.parse(step.expectedPhrases);
            }
          } catch (e) {
            this.$message.error(`步骤${i + 1}的关键词或短语格式错误，请使用JSON格式`);
            return;
          }
        }
        
        this.loading = true;
        await new Promise((resolve, reject) => {
          Api.scenario.saveScenarioSteps(this.scenarioId, this.steps, (res) => {
            if (res.code === 0) {
              resolve(res);
            } else {
              reject(new Error(res.msg));
            }
          });
        });
        
        this.$message.success('步骤配置保存成功');
      } catch (error) {
        this.$message.error('保存失败: ' + error.message);
        console.error('保存步骤失败:', error);
      } finally {
        this.loading = false;
      }
    },
    
    importStepTemplate() {
      this.templateDialogVisible = true;
    },
    
    selectTemplate(template) {
      const newStep = {
        id: this.generateId(),
        stepName: template.templateName,
        aiMessage: template.aiMessage || '',
        expectedKeywords: template.expectedKeywords || '[]',
        expectedPhrases: template.expectedPhrases || '[]',
        successCondition: template.successCondition || 'partial',
        maxAttempts: 3,
        timeoutSeconds: 10,
        alternativeMessage: template.alternativeMessage || '',
        gestureHint: '',
        musicEffect: '',
        stepType: 'normal',
        stepOrder: this.steps.length + 1,
        nextStepId: '',
        retryStepId: ''
      };
      this.steps.push(newStep);
      this.templateDialogVisible = false;
      this.$message.success('模板导入成功');
    },
    
    goBack() {
      this.$router.go(-1);
    },
    
    generateId() {
      return 'step_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },
    
    getScenarioTypeLabel(type) {
      const typeMap = {
        'express_needs': '表达需求',
        'greeting': '问候语',
        'emotion': '情感表达',
        'social': '社交技能',
        'learning': '学习训练',
        'game': '游戏互动'
      };
      return typeMap[type] || type;
    },
    
    getTriggerTypeLabel(type) {
      const typeMap = {
        'voice': '语音触发',
        'visual': '视觉触发',
        'button': '按钮触发',
        'mixed': '混合触发'
      };
      return typeMap[type] || type;
    },
    
    getStepTypeLabel(type) {
      const typeMap = {
        'normal': '普通步骤',
        'optional': '可选步骤',
        'branch': '分支步骤'
      };
      return typeMap[type] || type;
    },
    
    getStepTypeColor(type) {
      const colorMap = {
        'normal': '',
        'optional': 'warning',
        'branch': 'success'
      };
      return colorMap[type] || '';
    }
  }
}
</script>

<style scoped>
.scenario-step-config {
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

.scenario-info-card {
  margin-bottom: 20px;
}

.scenario-info {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-item .label {
  font-weight: bold;
  color: #606266;
  margin-right: 8px;
}

.info-item .value {
  color: #303133;
}

.step-list {
  margin-top: 20px;
}

.step-card {
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.step-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.step-number {
  font-weight: bold;
  color: #409EFF;
  font-size: 16px;
}

.step-name-input {
  width: 200px;
}

.step-actions {
  display: flex;
  gap: 5px;
}

.step-content {
  padding: 10px 0;
}

.form-item {
  margin-bottom: 15px;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
}

.template-list {
  max-height: 400px;
  overflow-y: auto;
}

.el-table {
  cursor: pointer;
}

.el-table .el-table__row:hover {
  background-color: #f5f7fa;
}
</style> 