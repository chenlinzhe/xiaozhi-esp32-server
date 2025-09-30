<template>
  <div class="scenario-step-config">
    <HeaderBar />

    <div class="operation-bar">
      <h2 class="page-title">对话步骤配置 - {{ scenario.scenarioName }}</h2>
      <div class="right-operations">
        <el-button type="primary" @click="addStep">添加步骤</el-button>
        <el-button @click="importStepTemplate">导入步骤模板</el-button>
        <el-button @click="saveSteps">保存配置</el-button>
        <el-button type="warning" @click="testApiConnection">测试API</el-button>
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
            <el-form :model="step" label-width="120px">
              <el-row :gutter="20">
                <el-col :span="24">
                  <el-form-item label="消息模式" class="form-item">
                    <el-radio-group v-model="step.useMessageList" @change="onMessageModeChange(step)">
                      <el-radio :label="0">单个消息</el-radio>
                      <el-radio :label="1">消息列表</el-radio>
                    </el-radio-group>
                  </el-form-item>
                </el-col>
              </el-row>

              <!-- 单个消息模式已删除，只使用消息列表模式 -->
              <div v-if="step.useMessageList === 0">
                <el-row :gutter="20">
                  <el-col :span="24">
                    <el-alert
                      title="提示"
                      type="info"
                      description="单个消息模式已废弃，请使用消息列表模式进行配置。"
                      show-icon
                      :closable="false">
                    </el-alert>
                  </el-col>
                </el-row>
              </div>

              <!-- 消息列表模式 -->
              <div v-if="step.useMessageList === 1" class="message-list-container">
                <StepMessageList
                  :step-id="step.stepId || 'temp_' + $index"
                  :scenario-id="scenario.id"
                  :initial-messages="step.stepMessages || []"
                  @messages-saved="onMessagesSaved"
                />
              </div>

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
                <el-col :span="6">
                  <el-form-item label="最大尝试次数" class="form-item">
                    <el-input-number
                      v-model="step.maxAttempts"
                      :min="1"
                      :max="10"
                      size="small" />
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="超时时间(秒)" class="form-item">
                    <el-input-number
                      v-model="step.timeoutSeconds"
                      :min="5"
                      :max="60"
                      size="small" />
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="语速配置" class="form-item">
                    <el-select v-model="step.speechRate" placeholder="请选择语速" size="small">
                      <el-option label="0.5倍速(慢)" :value="0.5" />
                      <el-option label="0.8倍速(稍慢)" :value="0.8" />
                      <el-option label="1.0倍速(正常)" :value="1.0" />
                      <el-option label="1.2倍速(稍快)" :value="1.2" />
                      <el-option label="1.5倍速(快)" :value="1.5" />
                      <el-option label="2.0倍速(很快)" :value="2.0" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
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

              <!-- 教学相关配置 -->
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="正确答案" class="form-item">
                    <el-input
                      v-model="step.correctResponse"
                      placeholder="正确答案，用于教学模式判断" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="等待时间(秒)" class="form-item">
                    <el-input-number
                      v-model="step.waitTimeSeconds"
                      :min="5"
                      :max="60"
                      size="small" />
                  </el-form-item>
                </el-col>
              </el-row>

              <!-- 已删除夸奖消息和鼓励消息配置 -->

              <el-row :gutter="20">
                <el-col :span="24">
                  <el-form-item label="超时自动回复" class="form-item">
                    <el-input
                      type="textarea"
                      v-model="step.autoReplyOnTimeout"
                      :rows="2"
                      placeholder="超时时的自动回复内容" />
                  </el-form-item>
                </el-col>
              </el-row>

              <!-- 成功条件分支配置 -->
              <el-row :gutter="20">
                <el-col :span="24">
                  <el-divider content-position="left">
                    <span class="divider-title">成功条件分支配置</span>
                  </el-divider>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="完全匹配分支" class="form-item">
                    <el-select
                      v-model="step.exactMatchStepId"
                      placeholder="请选择完全匹配时的下一步骤"
                      clearable
                      filterable>
                      <el-option
                        v-for="option in getStepOptions(index)"
                        :key="option.value"
                        :label="option.label"
                        :value="option.value">
                        <div class="step-option">
                          <span class="step-option-label">{{ option.label.split(' (')[0] }}</span>
                          <span class="step-option-id">{{ option.label.split(' (')[1].replace(')', '') }}</span>
                        </div>
                      </el-option>
                    </el-select>
                    <div class="form-tip">
                      <i class="el-icon-success"></i>
                      用户回答完全正确时跳转的步骤
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="部分匹配分支" class="form-item">
                    <el-select
                      v-model="step.partialMatchStepId"
                      placeholder="请选择部分匹配时的下一步骤"
                      clearable
                      filterable>
                      <el-option
                        v-for="option in getStepOptions(index)"
                        :key="option.value"
                        :label="option.label"
                        :value="option.value">
                        <div class="step-option">
                          <span class="step-option-label">{{ option.label.split(' (')[0] }}</span>
                          <span class="step-option-id">{{ option.label.split(' (')[1].replace(')', '') }}</span>
                        </div>
                      </el-option>
                    </el-select>
                    <div class="form-tip">
                      <i class="el-icon-warning"></i>
                      用户回答部分正确时跳转的步骤
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="完全不匹配分支" class="form-item">
                    <el-select
                      v-model="step.noMatchStepId"
                      placeholder="请选择完全不匹配时的下一步骤"
                      clearable
                      filterable>
                      <el-option
                        v-for="option in getStepOptions(index)"
                        :key="option.value"
                        :label="option.label"
                        :value="option.value">
                        <div class="step-option">
                          <span class="step-option-label">{{ option.label.split(' (')[0] }}</span>
                          <span class="step-option-id">{{ option.label.split(' (')[1].replace(')', '') }}</span>
                        </div>
                      </el-option>
                    </el-select>
                    <div class="form-tip">
                      <i class="el-icon-error"></i>
                      用户回答完全错误时跳转的步骤
                    </div>
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
                    <el-select
                      v-model="step.nextStepId"
                      placeholder="请选择下一步骤，留空则按顺序执行"
                      clearable
                      filterable>
                      <el-option
                        v-for="option in getStepOptions(index)"
                        :key="option.value"
                        :label="option.label"
                        :value="option.value">
                        <div class="step-option">
                          <span class="step-option-label">{{ option.label.split(' (')[0] }}</span>
                          <span class="step-option-id">{{ option.label.split(' (')[1].replace(')', '') }}</span>
                        </div>
                      </el-option>
                    </el-select>
                    <div class="form-tip">
                      <i class="el-icon-info"></i>
                      选择下一步骤可以实现跳转逻辑，留空则按步骤顺序执行（兼容旧版本）
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
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
import Api from '@/apis/module/scenario';
import { isApiSuccess, getBusinessData, getErrorMessage, ApiLogger } from '@/utils/apiHelper';
import HeaderBar from '@/components/HeaderBar.vue';
import StepMessageList from '@/components/StepMessageList.vue';

export default {
  name: 'ScenarioStepConfig',
  components: { HeaderBar, StepMessageList },
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
  computed: {
    // 计算所有步骤的选项，用于下一步骤选择
    allStepOptions() {
      const options = [];
      this.steps.forEach((step, index) => {
        const stepName = step.stepName || `步骤${index + 1}`;
        // 对于已保存的步骤使用ID，对于未保存的步骤使用索引
        const stepId = step.id || `temp_${index}`;
        options.push({
          label: `${stepName} (步骤${index + 1})`,
          value: stepId,
          index: index
        });
      });
      return options;
    }
  },
  methods: {
    async loadScenarioData() {
      try {
        this.loading = true;
        const [scenarioRes, stepsRes] = await Promise.all([
          this.getScenarioData(),
          this.getScenarioStepsData()
        ]);

        // 使用API辅助工具处理响应
        if (isApiSuccess(scenarioRes)) {
          this.scenario = getBusinessData(scenarioRes);
          ApiLogger.log('场景数据加载成功:', this.scenario);
        } else {
          throw new Error(getErrorMessage(scenarioRes, '获取场景数据失败'));
        }

        if (isApiSuccess(stepsRes)) {
          this.steps = getBusinessData(stepsRes) || [];
          ApiLogger.log('步骤数据加载成功:', this.steps);
        } else {
          throw new Error(getErrorMessage(stepsRes, '获取步骤数据失败'));
        }

      } catch (error) {
        ApiLogger.error('加载场景数据失败:', error);
        this.$message.error('加载场景数据失败: ' + error.message);
      } finally {
        this.loading = false;
      }
    },

    getScenarioData() {
      return new Promise((resolve, reject) => {
        Api.getScenario(this.scenarioId, (res) => {
          if (isApiSuccess(res)) {
            resolve(res);
          } else {
            reject(new Error(getErrorMessage(res, '获取场景数据失败')));
          }
        });
      });
    },

    getScenarioStepsData() {
      return new Promise((resolve, reject) => {
        // 优先使用包含消息的API，如果失败则回退到普通API
        Api.getScenarioStepsWithMessages(this.scenarioId, (res) => {
          if (isApiSuccess(res)) {
            resolve(res);
          } else {
            // 如果包含消息的API失败，回退到普通API
            Api.getScenarioSteps(this.scenarioId, (fallbackRes) => {
              if (isApiSuccess(fallbackRes)) {
                resolve(fallbackRes);
              } else {
                reject(new Error(getErrorMessage(fallbackRes, '获取步骤数据失败')));
              }
            });
          }
        });
      });
    },

    async loadStepTemplates() {
      try {
        Api.getStepTemplateList((res) => {
          if (isApiSuccess(res)) {
            this.stepTemplates = getBusinessData(res) || [];
            ApiLogger.log('步骤模板加载成功:', this.stepTemplates);
          } else {
            ApiLogger.error('加载步骤模板失败:', getErrorMessage(res));
          }
        });
      } catch (error) {
        ApiLogger.error('加载步骤模板失败:', error);
      }
    },

    addStep() {
      try {
        const newStep = {
          // 移除id字段，让后端自动生成
          stepName: `步骤${this.steps.length + 1}`,
          useMessageList: 1, // 默认使用消息列表模式
          messageListConfig: '', // 消息列表配置
          stepMessages: [], // 步骤消息列表
          expectedKeywords: '[]',
          expectedPhrases: '[]',
          successCondition: 'partial',
          speechRate: 1.0, // 默认正常语速
          exactMatchStepId: '', // 完全匹配分支
          partialMatchStepId: '', // 部分匹配分支
          noMatchStepId: '', // 完全不匹配分支
          maxAttempts: 3,
          timeoutSeconds: 10,
          correctResponse: '', // 正确答案
          autoReplyOnTimeout: '', // 超时自动回复
          waitTimeSeconds: 10, // 等待时间
          gestureHint: '',
          musicEffect: '',
          stepType: 'normal',
          stepOrder: this.steps.length + 1,
          nextStepId: '', // 兼容旧版本
          retryStepId: '',
          isOptional: 0, // 默认必需步骤
          branchCondition: '' // 分支条件
        };
        this.steps.push(newStep);
        this.$message.success('步骤添加成功');
      } catch (error) {
        ApiLogger.error('添加步骤失败:', error);
        this.$message.error('添加步骤失败: ' + error.message);
      }
    },

    removeStep(index) {
      this.$confirm('确定要删除这个步骤吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        try {
          // 使用Vue.set确保响应式更新
          this.$set(this.steps, index, null);
          this.steps.splice(index, 1);
          this.updateStepOrder();
          this.$message.success('步骤删除成功');
        } catch (error) {
          ApiLogger.error('删除步骤失败:', error);
          this.$message.error('删除步骤失败: ' + error.message);
        }
      }).catch(() => {
        // 用户取消删除
      });
    },

    moveStep(index, direction) {
      const newIndex = index + direction;
      if (newIndex >= 0 && newIndex < this.steps.length) {
        try {
          const temp = this.steps[index];
          this.$set(this.steps, index, this.steps[newIndex]);
          this.$set(this.steps, newIndex, temp);
          this.updateStepOrder();
          this.$message.success('步骤移动成功');
        } catch (error) {
          ApiLogger.error('移动步骤失败:', error);
          this.$message.error('移动步骤失败: ' + error.message);
        }
      }
    },

    updateStepOrder() {
      this.steps.forEach((step, index) => {
        if (step) {
          this.$set(step, 'stepOrder', index + 1);
        }
      });
    },

    onMessageModeChange(step) {
      // 当切换到消息列表模式时，初始化消息列表
      if (step.useMessageList === 1 && (!step.stepMessages || step.stepMessages.length === 0)) {
        // 初始化空的消息列表
        step.stepMessages = [];
      }
    },

    onMessagesSaved(messages) {
      // 当消息列表保存成功后，更新步骤的消息列表
      this.$message.success('消息列表保存成功');
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

          // 根据消息模式验证
          if (step.useMessageList === 0) {
            // 单个消息模式已废弃
            this.$message.error(`步骤${i + 1}：单个消息模式已废弃，请使用消息列表模式`);
            return;
          } else if (step.useMessageList === 1) {
            // // 消息列表模式
            // if (!step.stepMessages || step.stepMessages.length === 0) {
            //   this.$message.error(`步骤${i + 1}的消息列表不能为空`);
            //   return;
            // }
            // 验证每个消息
            for (let j = 0; j < step.stepMessages.length; j++) {
              const message = step.stepMessages[j];
              if (!message.messageContent.trim()) {
                this.$message.error(`步骤${i + 1}的消息${j + 1}内容不能为空`);
                return;
              }
            }
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

        // 处理临时ID的转换
        const stepsToSave = this.steps.map(step => {
          const stepCopy = { ...step };
          // 如果nextStepId是临时ID，需要转换为实际的步骤索引
          if (stepCopy.nextStepId && stepCopy.nextStepId.startsWith('temp_')) {
            const tempIndex = parseInt(stepCopy.nextStepId.replace('temp_', ''));
            // 临时ID将在保存后被实际ID替换
            stepCopy.nextStepId = null; // 先设为null，保存后再更新
          }
          return stepCopy;
        });

        // 记录临时ID到实际步骤的映射关系
        const tempIdMapping = {};
        this.steps.forEach((step, index) => {
          if (step.nextStepId && step.nextStepId.startsWith('temp_')) {
            tempIdMapping[index] = step.nextStepId;
          }
        });

        this.loading = true;
        const saveResult = await new Promise((resolve, reject) => {
          Api.saveScenarioSteps(this.scenarioId, stepsToSave, (res) => {
            if (isApiSuccess(res)) {
              resolve(res);
            } else {
              reject(new Error(getErrorMessage(res, '保存失败')));
            }
          });
        });

        // 保存成功后，重新加载步骤数据以获取正确的ID
        await this.loadScenarioData();

        // 更新临时ID映射
        this.updateTempIdMapping(tempIdMapping);

        this.$message.success('步骤配置保存成功');
        ApiLogger.log('步骤配置保存成功');
      } catch (error) {
        ApiLogger.error('保存步骤失败:', error);
        this.$message.error('保存失败: ' + error.message);
      } finally {
        this.loading = false;
      }
    },

    importStepTemplate() {
      this.templateDialogVisible = true;
    },

    selectTemplate(template) {
      const newStep = {
        // 移除id字段，让后端自动生成
        stepName: template.templateName,
        useMessageList: 1, // 默认使用消息列表模式
        messageListConfig: '', // 消息列表配置
        stepMessages: [], // 步骤消息列表
        expectedKeywords: template.expectedKeywords || '[]',
        expectedPhrases: template.expectedPhrases || '[]',
        successCondition: template.successCondition || 'partial',
        maxAttempts: 3,
        timeoutSeconds: 10,
        correctResponse: '', // 正确答案
        autoReplyOnTimeout: '', // 超时自动回复
        waitTimeSeconds: 10, // 等待时间
        gestureHint: '',
        musicEffect: '',
        stepType: 'normal',
        stepOrder: this.steps.length + 1,
        nextStepId: '',
        retryStepId: '',
        isOptional: 0, // 默认必需步骤
        branchCondition: '' // 分支条件
      };
      this.steps.push(newStep);
      this.templateDialogVisible = false;
      this.$message.success('模板导入成功');
    },

    goBack() {
      this.$router.go(-1);
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
    },

    testApiConnection() {
      ApiLogger.log('开始测试API连接');

      // 测试获取场景数据
      Api.getScenario(this.scenarioId, (res) => {
        ApiLogger.log('场景数据API测试响应:', res);
        if (isApiSuccess(res)) {
          const data = getBusinessData(res);
          ApiLogger.log('场景数据获取成功:', data);
          this.$message.success('场景数据API测试成功');
        } else {
          const errorMsg = getErrorMessage(res, '场景数据API测试失败');
          ApiLogger.error('场景数据API测试失败:', errorMsg);
          this.$message.error(errorMsg);
        }
      });

      // 测试获取步骤数据
      Api.getScenarioSteps(this.scenarioId, (res) => {
        ApiLogger.log('步骤数据API测试响应:', res);
        if (isApiSuccess(res)) {
          const data = getBusinessData(res);
          ApiLogger.log('步骤数据获取成功:', data);
          this.$message.success('步骤数据API测试成功');
        } else {
          const errorMsg = getErrorMessage(res, '步骤数据API测试失败');
          ApiLogger.error('步骤数据API测试失败:', errorMsg);
          this.$message.error(errorMsg);
        }
      });
    },

    getStepOptions(currentStepIndex) {
      return this.allStepOptions.filter(option => option.index !== currentStepIndex);
    },

    // 更新临时ID映射
    updateTempIdMapping(tempIdMapping) {
      Object.keys(tempIdMapping).forEach(stepIndex => {
        const tempId = tempIdMapping[stepIndex];
        const targetTempIndex = parseInt(tempId.replace('temp_', ''));

        // 找到对应的实际步骤ID
        if (this.steps[targetTempIndex] && this.steps[targetTempIndex].id) {
          this.steps[stepIndex].nextStepId = this.steps[targetTempIndex].id;
        }
      });
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

/* 步骤选择下拉框样式 */
.step-select-dropdown {
  .el-select-dropdown__item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}

/* 步骤选项样式 */
.step-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.step-option-label {
  font-weight: 500;
  color: #303133;
}

.step-option-id {
  color: #909399;
  font-size: 12px;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
}

/* 表单提示信息样式 */
.form-tip {
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.form-tip i {
  margin-right: 4px;
  color: #409EFF;
}

/* 新增字段样式 */
.divider-title {
  font-weight: 600;
  color: #409EFF;
  font-size: 14px;
}

/* 分支配置区域样式 */
.branch-config-section {
  background-color: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
  margin: 15px 0;
  border-left: 4px solid #409EFF;
}

/* 教学配置区域样式 */
.teaching-config-section {
  background-color: #f0f9ff;
  border-radius: 6px;
  padding: 15px;
  margin: 15px 0;
  border-left: 4px solid #67c23a;
}

/* 语速配置样式 */
.speech-rate-config {
  .el-select {
    width: 100%;
  }
}

/* 成功条件分支样式 */
.success-condition-branch {
  .el-form-item {
    margin-bottom: 20px;
  }
}

/* 消息列表容器样式 */
.message-list-container {
  margin: 15px 0;
  position: relative;
  z-index: 1;
}

/* 确保消息列表不会遮挡其他内容 */
.message-list-container + .el-row {
  margin-top: 20px;
  position: relative;
  z-index: 2;
}
</style>
