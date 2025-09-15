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
      
      <!-- 表格显示消息列表 -->
      <el-table 
        v-else
        :data="messages" 
        stripe
        border
        size="small"
        class="message-table"
        :row-class-name="getRowClassName"
        row-key="messageOrder"
      >
        <el-table-column prop="messageOrder" label="序号" width="60" align="center">
          <template slot-scope="scope">
            <span class="message-order">{{ scope.row.messageOrder }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="拖拽" width="50" align="center">
          <template slot-scope="scope">
            <div 
              class="drag-handle" 
              draggable="true"
              @dragstart="handleDragStart(scope.$index, $event)"
              @dragover="handleDragOver($event)"
              @drop="handleDrop(scope.$index, $event)"
              @dragend="handleDragEnd"
            >
              <i class="el-icon-rank drag-icon"></i>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="messageContent" label="消息内容" min-width="200">
          <template slot-scope="scope">
            <div class="message-content-cell">
              <span class="content-text" :title="scope.row.messageContent">
                {{ scope.row.messageContent.length > 50 ? scope.row.messageContent.substring(0, 50) + '...' : scope.row.messageContent }}
              </span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="messageType" label="消息类型" width="100" align="center">
          <template slot-scope="scope">
            <el-tag :type="getMessageTypeColor(scope.row.messageType)" size="mini">
              {{ getMessageTypeLabel(scope.row.messageType) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="speechRate" label="语速" width="80" align="center">
          <template slot-scope="scope">
            <span class="speech-rate">{{ scope.row.speechRate }}x</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="waitTimeSeconds" label="等待时间" width="80" align="center">
          <template slot-scope="scope">
            <span class="wait-time">{{ scope.row.waitTimeSeconds }}s</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="isActive" label="状态" width="80" align="center">
          <template slot-scope="scope">
            <el-tag :type="scope.row.isActive ? 'success' : 'danger'" size="mini">
              {{ scope.row.isActive ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="220" align="center" fixed="right">
          <template slot-scope="scope">
            <div class="table-actions">
              <el-button size="mini" type="primary" @click="editMessage(scope.$index)" title="编辑消息">
                <i class="el-icon-edit"></i>
              </el-button>
              <el-button size="mini" @click="moveMessage(scope.$index, -1)" :disabled="scope.$index === 0" title="上移">
                <i class="el-icon-arrow-up"></i>
              </el-button>
              <el-button size="mini" @click="moveMessage(scope.$index, 1)" :disabled="scope.$index === messages.length - 1" title="下移">
                <i class="el-icon-arrow-down"></i>
              </el-button>
              <el-button size="mini" type="danger" @click="removeMessage(scope.$index)" title="删除">
                <i class="el-icon-delete"></i>
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="message-list-footer">
      <el-button @click="saveMessages" type="primary" :loading="saving">
        保存消息列表
      </el-button>
      <el-button @click="resetMessages">重置</el-button>
    </div>

    <!-- 消息编辑弹出框 -->
    <el-dialog
      :title="editingMessage ? '编辑消息' : '添加消息'"
      :visible.sync="dialogVisible"
      width="90%"
      :max-width="800"
      top="5vh"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :modal="true"
      :append-to-body="true"
      :destroy-on-close="false"
      custom-class="message-edit-dialog"
    >
      <el-form :model="currentMessage" :rules="messageRules" ref="messageForm" label-width="100px" size="small">
        <el-row :gutter="15">
          <el-col :span="24">
            <el-form-item label="消息内容" prop="messageContent">
              <el-input 
                type="textarea" 
                v-model="currentMessage.messageContent" 
                :rows="3"
                placeholder="请输入AI要说的内容，支持使用 **{childName}** 替换儿童姓名" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="15">
          <el-col :span="12">
            <el-form-item label="消息类型" prop="messageType">
              <el-select v-model="currentMessage.messageType" placeholder="请选择消息类型" style="width: 100%">
                <el-option label="普通消息" value="normal" />
                <el-option label="指令消息" value="instruction" />
                <el-option label="鼓励消息" value="encouragement" />
                <el-option label="反馈消息" value="feedback" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="语速配置" prop="speechRate">
              <el-select v-model="currentMessage.speechRate" placeholder="请选择语速" style="width: 100%">
                <el-option label="0.2倍速(很慢)" :value="0.2" />
                <el-option label="0.5倍速(慢)" :value="0.5" />
                <el-option label="0.8倍速(稍慢)" :value="0.8" />
                <el-option label="1.0倍速(正常)" :value="1.0" />
                <el-option label="1.2倍速(稍快)" :value="1.2" />
                <el-option label="1.5倍速(快)" :value="1.5" />
                <el-option label="2.0倍速(很快)" :value="2.0" />
                <el-option label="2.5倍速(极快)" :value="2.5" />
                <el-option label="3.0倍速(最快)" :value="3.0" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="15">
          <el-col :span="12">
            <el-form-item label="等待时间(秒)" prop="waitTimeSeconds">
              <el-input-number 
                v-model="currentMessage.waitTimeSeconds" 
                :min="1" 
                :max="30"
                style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="是否启用">
              <el-switch 
                v-model="currentMessage.isActive" 
                :active-value="1" 
                :inactive-value="0"
                active-text="启用"
                inactive-text="禁用" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="15">
          <el-col :span="24">
            <el-form-item label="消息参数">
              <el-input 
                type="textarea" 
                v-model="currentMessage.parameters" 
                :rows="2"
                placeholder="JSON格式，如：{'emotion': 'happy', 'tone': 'gentle'}" />
              <div class="hint-text">可选参数：emotion(情绪)、tone(语调)、volume(音量)等</div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <div slot="footer" class="dialog-footer">
        <el-button @click="cancelEdit">取消</el-button>
        <el-button type="primary" @click="confirmEdit" :loading="saving">确定</el-button>
      </div>
    </el-dialog>
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
      originalMessages: [],
      dialogVisible: false,
      editingMessage: false,
      editingIndex: -1,
      currentMessage: {
        messageId: '',
        stepId: '',
        scenarioId: '',
        messageContent: '',
        messageOrder: 1,
        speechRate: 1.0,
        waitTimeSeconds: 3,
        parameters: '{"emotion": "friendly", "tone": "gentle"}',
        isActive: 1,
        messageType: 'normal'
      },
      messageRules: {
        messageContent: [
          { required: true, message: '请输入消息内容', trigger: 'blur' }
        ],
        messageType: [
          { required: true, message: '请选择消息类型', trigger: 'change' }
        ],
        speechRate: [
          { required: true, message: '请选择语速', trigger: 'change' }
        ],
        waitTimeSeconds: [
          { required: true, message: '请输入等待时间', trigger: 'blur' }
        ]
      },
      // 拖拽相关
      dragIndex: -1
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
      this.editingMessage = false;
      this.editingIndex = -1;
      this.currentMessage = {
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
      this.dialogVisible = true;
    },

    editMessage(index) {
      this.editingMessage = true;
      this.editingIndex = index;
      this.currentMessage = JSON.parse(JSON.stringify(this.messages[index]));
      this.dialogVisible = true;
    },

    confirmEdit() {
      this.$refs.messageForm.validate((valid) => {
        if (valid) {
          // 验证JSON格式
          try {
            if (this.currentMessage.parameters && this.currentMessage.parameters.trim()) {
              JSON.parse(this.currentMessage.parameters);
            }
          } catch (e) {
            this.$message.error('消息参数格式错误，请使用JSON格式');
            return;
          }

          if (this.editingMessage) {
            // 编辑现有消息
            this.$set(this.messages, this.editingIndex, JSON.parse(JSON.stringify(this.currentMessage)));
            this.$message.success('消息修改成功');
          } else {
            // 添加新消息
            this.messages.push(JSON.parse(JSON.stringify(this.currentMessage)));
            this.updateMessageOrder();
            this.$message.success('消息添加成功');
          }
          
          this.dialogVisible = false;
          this.resetCurrentMessage();
        } else {
          this.$message.error('请填写完整信息');
        }
      });
    },

    cancelEdit() {
      this.dialogVisible = false;
      this.resetCurrentMessage();
    },

    resetCurrentMessage() {
      this.editingMessage = false;
      this.editingIndex = -1;
      this.currentMessage = {
        messageId: '',
        stepId: this.stepId,
        scenarioId: this.scenarioId,
        messageContent: '',
        messageOrder: 1,
        speechRate: 1.0,
        waitTimeSeconds: 3,
        parameters: '{"emotion": "friendly", "tone": "gentle"}',
        isActive: 1,
        messageType: 'normal'
      };
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
    },

    // 获取消息类型标签
    getMessageTypeLabel(type) {
      const typeMap = {
        'normal': '普通',
        'instruction': '指令',
        'encouragement': '鼓励',
        'feedback': '反馈'
      };
      return typeMap[type] || '普通';
    },

    // 获取消息类型颜色
    getMessageTypeColor(type) {
      const colorMap = {
        'normal': '',
        'instruction': 'primary',
        'encouragement': 'success',
        'feedback': 'warning'
      };
      return colorMap[type] || '';
    },

    // 获取表格行类名
    getRowClassName({ row, rowIndex }) {
      if (row.isActive === 0) {
        return 'disabled-row';
      }
      return '';
    },

    // 开始拖拽
    handleDragStart(index, event) {
      this.dragIndex = index;
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/html', index);
      
      // 添加拖拽样式
      event.target.style.opacity = '0.5';
    },

    // 处理拖拽悬停
    handleDragOver(event) {
      event.preventDefault();
      event.dataTransfer.dropEffect = 'move';
    },

    // 处理拖拽放置
    handleDrop(targetIndex, event) {
      event.preventDefault();
      
      const sourceIndex = parseInt(event.dataTransfer.getData('text/html'));
      
      if (sourceIndex !== targetIndex) {
        this.moveMessageByDrag(sourceIndex, targetIndex);
      }
    },

    // 处理拖拽结束
    handleDragEnd(event) {
      // 恢复样式
      event.target.style.opacity = '1';
      
      // 重置拖拽状态
      this.dragIndex = -1;
    },

    // 通过拖拽移动消息
    moveMessageByDrag(fromIndex, toIndex) {
      const message = this.messages.splice(fromIndex, 1)[0];
      this.messages.splice(toIndex, 0, message);
      this.updateMessageOrder();
      this.$message.success('消息顺序已更新');
    }
  }
}
</script>

<style scoped>
.step-message-list {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  margin-top: 12px;
  margin-bottom: 12px;
  background-color: #fafafa;
}

.message-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.message-list-header h4 {
  margin: 0;
  color: #303133;
}

.message-list-content {
  min-height: 150px;
  max-height: 300px;
  overflow-y: auto;
}

/* 表格样式 */
.message-table {
  width: 100%;
}

.message-table .message-order {
  font-weight: 600;
  color: #409eff;
  font-size: 14px;
}

.message-content-cell {
  max-width: 200px;
}

.content-text {
  display: block;
  word-break: break-all;
  line-height: 1.4;
}

.speech-rate, .wait-time {
  font-weight: 500;
  color: #606266;
}

.table-actions {
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
  align-items: center;
}

.table-actions .el-button {
  margin: 0;
  padding: 5px 8px;
  font-size: 12px;
  min-width: 28px;
  height: 28px;
  border-radius: 4px;
}

/* 禁用行样式 */
.message-table >>> .disabled-row {
  background-color: #f5f7fa;
  color: #c0c4cc;
}

.message-table >>> .disabled-row td {
  background-color: #f5f7fa !important;
  color: #c0c4cc !important;
}

.message-list-footer {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid #e4e7ed;
  text-align: center;
}

.hint-text {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 弹出框样式 */
.dialog-footer {
  text-align: right;
}

.dialog-footer .el-button {
  margin-left: 10px;
}

/* 自定义弹出框样式 */
.message-edit-dialog {
  max-height: 90vh;
  overflow-y: auto;
}

.message-edit-dialog >>> .el-dialog {
  margin-top: 5vh !important;
  margin-bottom: 5vh !important;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.message-edit-dialog >>> .el-dialog__body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  max-height: calc(90vh - 120px);
}

.message-edit-dialog >>> .el-dialog__header {
  padding: 20px 20px 10px 20px;
  border-bottom: 1px solid #e4e7ed;
}

.message-edit-dialog >>> .el-dialog__footer {
  padding: 10px 20px 20px 20px;
  border-top: 1px solid #e4e7ed;
  background-color: #fafafa;
}

/* 响应式弹出框 */
@media (max-width: 768px) {
  .message-edit-dialog >>> .el-dialog {
    width: 95% !important;
    margin: 2vh auto !important;
  }
  
  .message-edit-dialog >>> .el-dialog__body {
    padding: 15px;
  }
  
  .message-edit-dialog >>> .el-form-item__label {
    width: 100px !important;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .table-actions {
    flex-direction: row;
    gap: 4px;
    flex-wrap: wrap;
  }
  
  .table-actions .el-button {
    min-width: 24px;
    height: 24px;
    padding: 3px 6px;
    font-size: 11px;
  }
  
  .message-content-cell {
    max-width: 150px;
  }
}

@media (max-width: 480px) {
  .table-actions {
    flex-direction: column;
    gap: 2px;
  }
  
  .table-actions .el-button {
    width: 100%;
    margin: 1px 0;
    min-width: auto;
  }
}

/* 表格滚动条样式 */
.message-table >>> .el-table__body-wrapper {
  max-height: 200px;
  overflow-y: auto;
}

.message-table >>> .el-table__body-wrapper::-webkit-scrollbar {
  width: 6px;
}

.message-table >>> .el-table__body-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.message-table >>> .el-table__body-wrapper::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.message-table >>> .el-table__body-wrapper::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 确保消息列表组件不会遮挡其他内容 */
.step-message-list {
  position: relative;
  z-index: 1;
}

/* 当消息列表为空时，减少高度 */
.message-list-content:has(.el-empty) {
  min-height: 80px;
  max-height: 120px;
}

/* 优化表格行高 */
.message-table >>> .el-table__row {
  height: 40px;
}

.message-table >>> .el-table td {
  padding: 8px 0;
}

/* 紧凑的按钮样式 */
.message-list-header .el-button {
  padding: 6px 12px;
  font-size: 12px;
}

.message-list-footer .el-button {
  padding: 8px 16px;
  font-size: 13px;
}

/* 拖拽相关样式 */
.drag-handle {
  cursor: move;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  transition: all 0.3s ease;
  user-select: none;
}

.drag-handle:hover {
  background-color: #f0f0f0;
  border-radius: 4px;
}

.drag-icon {
  color: #909399;
  font-size: 16px;
  transition: color 0.3s ease;
}

.drag-handle:hover .drag-icon {
  color: #409eff;
}

/* 拖拽时的样式 */
.drag-handle[draggable="true"]:active {
  cursor: grabbing;
}

.drag-handle[draggable="true"]:hover {
  cursor: grab;
}
</style>
