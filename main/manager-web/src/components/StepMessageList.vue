<template>
  <div class="step-message-list">
    <div class="message-list-header">
      <h4>AI消息列表</h4>
      <el-button type="primary" size="small" @click="addMessage">
        <i class="el-icon-plus"></i> 添加消息
      </el-button>
    </div>

    <div class="message-list-content">
      <el-empty v-if="!messages || messages.length === 0" description="暂无消息，请添加AI消息" />
      
      <div v-else class="message-items">
        <div 
          v-for="(message, index) in messages" 
          :key="message.messageId || index"
          class="message-item"
        >
          <div class="message-header">
            <span class="message-order">消息 {{ index + 1 }}</span>
            <div class="message-actions">
              <el-button size="mini" @click="moveMessage(index, -1)" :disabled="index === 0">
                <i class="el-icon-arrow-up"></i>
              </el-button>
              <el-button size="mini" @click="moveMessage(index, 1)" :disabled="index === messages.length - 1">
                <i class="el-icon-arrow-down"></i>
              </el-button>
              <el-button size="mini" type="danger" @click="removeMessage(index)">
                <i class="el-icon-delete"></i>
              </el-button>
            </div>
          </div>

          <div class="message-content">
            <el-form :model="message" label-width="100px" size="small">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="消息内容">
                    <el-input 
                      type="textarea" 
                      v-model="message.messageContent" 
                      :rows="3"
                      placeholder="请输入AI要说的内容，支持使用 **{childName}** 替换儿童姓名" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="消息类型">
                    <el-select v-model="message.messageType" placeholder="请选择消息类型">
                      <el-option label="普通消息" value="normal" />
                      <el-option label="指令消息" value="instruction" />
                      <el-option label="鼓励消息" value="encouragement" />
                      <el-option label="反馈消息" value="feedback" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="语速配置">
                    <el-select v-model="message.speechRate" placeholder="请选择语速" size="small">
                      <el-option label="0.5倍速(慢)" :value="0.5" />
                      <el-option label="0.8倍速(稍慢)" :value="0.8" />
                      <el-option label="1.0倍速(正常)" :value="1.0" />
                      <el-option label="1.2倍速(稍快)" :value="1.2" />
                      <el-option label="1.5倍速(快)" :value="1.5" />
                      <el-option label="2.0倍速(很快)" :value="2.0" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="等待时间(秒)">
                    <el-input-number 
                      v-model="message.waitTimeSeconds" 
                      :min="1" 
                      :max="30"
                      size="small" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="是否启用">
                    <el-switch 
                      v-model="message.isActive" 
                      :active-value="1" 
                      :inactive-value="0"
                      active-text="启用"
                      inactive-text="禁用" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="24">
                  <el-form-item label="消息参数">
                    <el-input 
                      type="textarea" 
                      v-model="message.parameters" 
                      :rows="2"
                      placeholder="JSON格式，如：{'emotion': 'happy', 'tone': 'gentle'}" />
                    <div class="hint-text">可选参数：emotion(情绪)、tone(语调)、volume(音量)等</div>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>
        </div>
      </div>
    </div>

    <div class="message-list-footer">
      <el-button @click="saveMessages" type="primary" :loading="saving">
        保存消息列表
      </el-button>
      <el-button @click="resetMessages">重置</el-button>
    </div>
  </div>
</template>

<script>
import scenarioApi from '../apis/module/scenario.js';

export default {
  name: 'StepMessageList',
  props: {
    stepId: {
      type: String,
      required: true
    },
    scenarioId: {
      type: String,
      required: true
    },
    initialMessages: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      messages: [],
      saving: false,
      originalMessages: []
    }
  },
  watch: {
    initialMessages: {
      handler(newVal) {
        this.initializeMessages(newVal);
      },
      immediate: true
    },
    stepId: {
      handler(newVal) {
        if (newVal && newVal !== 'temp_' + this.$index) {
          this.loadMessagesFromServer();
        }
      },
      immediate: true
    }
  },
  methods: {
    initializeMessages(messages) {
      if (messages && messages.length > 0) {
        this.messages = JSON.parse(JSON.stringify(messages));
        this.originalMessages = JSON.parse(JSON.stringify(messages));
        console.log('初始化消息列表:', this.messages);
      } else {
        this.messages = [];
        this.originalMessages = [];
        console.log('消息列表为空，初始化为空数组');
      }
    },

    addMessage() {
      const newMessage = {
        messageId: '',
        stepId: this.stepId,
        scenarioId: this.scenarioId,
        messageContent: '',
        messageOrder: this.messages.length + 1,
        speechRate: 1.0,
        waitTimeSeconds: 3,
        parameters: '{"emotion": "friendly", "tone": "gentle"}',
        isActive: 1,
        messageType: 'normal'
      };
      this.messages.push(newMessage);
    },

    removeMessage(index) {
      this.$confirm('确定要删除这条消息吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.messages.splice(index, 1);
        this.updateMessageOrder();
        this.$message.success('消息删除成功');
      }).catch(() => {
        // 取消删除
      });
    },

    moveMessage(index, direction) {
      const newIndex = index + direction;
      if (newIndex >= 0 && newIndex < this.messages.length) {
        const temp = this.messages[index];
        this.messages[index] = this.messages[newIndex];
        this.messages[newIndex] = temp;
        this.updateMessageOrder();
      }
    },

    updateMessageOrder() {
      this.messages.forEach((message, index) => {
        message.messageOrder = index + 1;
      });
    },

    async saveMessages() {
      try {
        // 验证消息数据
        for (let i = 0; i < this.messages.length; i++) {
          const message = this.messages[i];
          if (!message.messageContent.trim()) {
            this.$message.error(`消息${i + 1}的内容不能为空`);
            return;
          }
          
          // 验证JSON格式
          try {
            if (message.parameters && message.parameters.trim()) {
              JSON.parse(message.parameters);
            }
          } catch (e) {
            this.$message.error(`消息${i + 1}的参数格式错误，请使用JSON格式`);
            return;
          }
        }

        this.saving = true;
        
        // 使用scenario API保存消息
        scenarioApi.saveStepMessages(this.stepId, this.messages, (response) => {
          if (response.data && (response.data.success || response.data.code === 0)) {
            this.$message.success('消息保存成功');
            this.originalMessages = JSON.parse(JSON.stringify(this.messages));
            this.$emit('messages-saved', this.messages);
          } else {
            this.$message.error(response.data?.msg || response.data?.message || '保存失败');
          }
          this.saving = false;
        });
        
      } catch (error) {
        console.error('保存消息失败:', error);
        this.$message.error('保存失败: ' + (error.message || '未知错误'));
        this.saving = false;
      }
    },

    resetMessages() {
      this.$confirm('确定要重置消息列表吗？未保存的更改将丢失。', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.initializeMessages(this.originalMessages);
        this.$message.info('消息列表已重置');
      }).catch(() => {
        // 取消重置
      });
    },

    getMessages() {
      return this.messages;
    },

    setMessages(messages) {
      this.initializeMessages(messages);
    },

    // 从服务器加载消息数据
    async loadMessagesFromServer() {
      if (!this.stepId || this.stepId.startsWith('temp_')) {
        return; // 临时步骤ID，不加载
      }

      try {
        // 调用API获取步骤消息列表
        scenarioApi.getStepMessages(this.stepId, (response) => {
          if (response.data && (response.data.success || response.data.code === 0)) {
            const messages = response.data.data || [];
            this.initializeMessages(messages);
            console.log('从服务器加载消息成功:', messages);
          } else {
            console.warn('从服务器加载消息失败:', response.data?.msg || '未知错误');
            // 如果加载失败，保持当前状态
          }
        });
      } catch (error) {
        console.error('加载消息失败:', error);
      }
    }
  }
}
</script>

<style scoped>
.step-message-list {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 16px;
  margin-top: 16px;
}

.message-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.message-list-header h4 {
  margin: 0;
  color: #303133;
}

.message-list-content {
  min-height: 200px;
}

.message-items {
  display: flex;
  column-gap: 16px;
  flex-direction: column;
}

.message-item {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 16px;
  background-color: #fafafa;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.message-order {
  font-weight: 600;
  color: #409eff;
}

.message-actions {
  display: flex;
  gap: 8px;
}

.message-content {
  background-color: white;
  padding: 16px;
  border-radius: 4px;
}

.message-list-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
  text-align: center;
}

.hint-text {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.el-form-item {
  margin-bottom: 16px;
}
</style>
