<template>
  <div class="scenario-edit">
    <HeaderBar />
    
    <div class="operation-bar">
      <h2 class="page-title">编辑场景</h2>
      <div class="right-operations">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="saveScenario">保存场景</el-button>
      </div>
    </div>
    
    <div class="main-wrapper">
      <el-form :model="scenarioForm" :rules="rules" ref="scenarioForm" label-width="120px" class="scenario-form">
        <el-card class="form-card">
          <div slot="header" class="card-header">
            <span>基本信息</span>
          </div>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="场景名称" prop="scenarioName">
                <el-input v-model="scenarioForm.scenarioName" placeholder="请输入场景名称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="场景编码" prop="scenarioCode">
                <el-input v-model="scenarioForm.scenarioCode" placeholder="请输入场景编码" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="场景类型" prop="scenarioType">
                <el-select v-model="scenarioForm.scenarioType" placeholder="请选择场景类型">
                  <el-option label="表达需求" value="express_needs" />
                  <el-option label="问候语" value="greeting" />
                  <el-option label="情感表达" value="emotion" />
                  <el-option label="社交技能" value="social" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="触发方式" prop="triggerType">
                <el-select v-model="scenarioForm.triggerType" placeholder="请选择触发方式">
                  <el-option label="语音触发" value="voice" />
                  <el-option label="视觉触发" value="visual" />
                  <el-option label="按钮触发" value="button" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="难度等级" prop="difficultyLevel">
                <el-rate v-model="scenarioForm.difficultyLevel" :max="5" show-text />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="目标年龄" prop="targetAge">
                <el-select v-model="scenarioForm.targetAge" placeholder="请选择目标年龄">
                  <el-option label="3-6岁" value="3-6" />
                  <el-option label="7-12岁" value="7-12" />
                  <el-option label="13-18岁" value="13-18" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="场景描述" prop="description">
            <el-input type="textarea" v-model="scenarioForm.description" rows="3" 
                      placeholder="请输入场景描述" />
          </el-form-item>
        </el-card>
        
        <el-card class="form-card">
          <div slot="header" class="card-header">
            <span>触发配置</span>
          </div>
          
          <el-form-item label="语音关键词" prop="triggerKeywords">
            <el-input type="textarea" v-model="scenarioForm.triggerKeywords" rows="3" 
                      placeholder="请输入语音触发关键词，多个关键词用逗号分隔" />
            <div class="hint-text">例如：渴了,口渴,喝水</div>
          </el-form-item>
          
          <el-form-item label="视觉卡片" prop="triggerCards">
            <el-input type="textarea" v-model="scenarioForm.triggerCards" rows="3" 
                      placeholder="请输入视觉触发卡片，JSON格式" />
            <div class="hint-text">例如：["card1.jpg", "card2.jpg"]</div>
          </el-form-item>
        </el-card>
        
        <el-card class="form-card">
          <div slot="header" class="card-header">
            <span>其他设置</span>
          </div>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="排序权重" prop="sortOrder">
                <el-input-number v-model="scenarioForm.sortOrder" :min="0" :max="999" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="用户回复次数限制" prop="maxUserReplies">
                <el-input-number 
                  v-model="scenarioForm.maxUserReplies" 
                  :min="1" 
                  :max="10"
                  placeholder="超过此次数就结束场景" />
                <div class="hint-text">默认3次，超过此次数就自动结束场景</div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="是否启用" prop="isActive">
                <el-switch v-model="scenarioForm.isActive" active-color="#13ce66" inactive-color="#ff4949" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>
      </el-form>
    </div>
  </div>
</template>

<script>
import Api from '@/apis/module/scenario';
import { isApiSuccess, getBusinessData, getErrorMessage, ApiLogger } from '@/utils/apiHelper';
import HeaderBar from '@/components/HeaderBar.vue';

export default {
  name: 'ScenarioEdit',
  components: { HeaderBar },
  data() {
    return {
      scenarioId: '',
      scenarioForm: {
        scenarioName: '',
        scenarioCode: '',
        scenarioType: '',
        triggerType: '',
        triggerKeywords: '',
        triggerCards: '',
        description: '',
        difficultyLevel: 1,
        targetAge: '',
        sortOrder: 0,
        maxUserReplies: 3,
        isActive: true
      },
      rules: {
        scenarioName: [
          { required: true, message: '请输入场景名称', trigger: 'blur' }
        ],
        scenarioCode: [
          { required: true, message: '请输入场景编码', trigger: 'blur' }
        ],
        scenarioType: [
          { required: true, message: '请选择场景类型', trigger: 'change' }
        ],
        triggerType: [
          { required: true, message: '请选择触发方式', trigger: 'change' }
        ],
        difficultyLevel: [
          { required: true, message: '请选择难度等级', trigger: 'change' }
        ],
        targetAge: [
          { required: true, message: '请选择目标年龄', trigger: 'change' }
        ]
      }
    }
  },
  mounted() {
    this.scenarioId = this.$route.params.id;
    this.loadScenarioData();
  },
  methods: {
    loadScenarioData() {
      Api.getScenario(this.scenarioId, (data) => {
        ApiLogger.log('获取场景详情响应:', data);
        
        if (isApiSuccess(data)) {
          const scenario = getBusinessData(data);
          
          if (scenario) {
            // 处理JSON格式的数据
            if (scenario.triggerKeywords) {
              try {
                const keywords = JSON.parse(scenario.triggerKeywords);
                scenario.triggerKeywords = keywords.join(', ');
              } catch (e) {
                // 如果不是JSON格式，直接使用
              }
            }
            
            if (scenario.triggerCards) {
              try {
                const cards = JSON.parse(scenario.triggerCards);
                scenario.triggerCards = JSON.stringify(cards, null, 2);
              } catch (e) {
                // 如果不是JSON格式，直接使用
              }
            }
            
            this.scenarioForm = { ...scenario };
            ApiLogger.log('场景数据加载成功:', this.scenarioForm);
          } else {
            this.$message.error('场景数据为空');
            ApiLogger.error('场景数据为空');
          }
        } else {
          const errorMsg = getErrorMessage(data, '加载场景数据失败');
          this.$message.error(errorMsg);
          ApiLogger.error('加载场景数据失败:', errorMsg);
        }
      });
    },
    
    goBack() {
      this.$router.go(-1);
    },
    
    saveScenario() {
      this.$refs.scenarioForm.validate((valid) => {
        if (valid) {
          // 处理触发关键词格式
          if (this.scenarioForm.triggerKeywords) {
            const keywords = this.scenarioForm.triggerKeywords.split(',').map(k => k.trim());
            this.scenarioForm.triggerKeywords = JSON.stringify(keywords);
          }
          
          // 处理视觉卡片格式
          if (this.scenarioForm.triggerCards) {
            try {
              const cards = JSON.parse(this.scenarioForm.triggerCards);
              this.scenarioForm.triggerCards = JSON.stringify(cards);
            } catch (e) {
              this.$message.error('视觉卡片格式错误，请使用JSON格式');
              return;
            }
          }
          
          Api.updateScenario(this.scenarioId, this.scenarioForm, (data) => {
            ApiLogger.log('更新场景响应:', data);
            
            if (isApiSuccess(data)) {
              this.$message.success('场景更新成功');
              this.$router.push('/scenario-config');
            } else {
              const errorMsg = getErrorMessage(data, '保存失败');
              this.$message.error(errorMsg);
              ApiLogger.error('保存场景失败:', errorMsg);
            }
          });
        } else {
          this.$message.error('请检查表单填写是否正确');
        }
      });
    }
  }
}
</script>

<style scoped>
.scenario-edit {
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
  max-width: 1200px;
  margin: 0 auto;
}

.scenario-form {
  margin-top: 20px;
}

.form-card {
  margin-bottom: 20px;
}

.card-header {
  font-weight: bold;
  color: #303133;
}

.hint-text {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.el-rate {
  margin-top: 5px;
}
</style>
