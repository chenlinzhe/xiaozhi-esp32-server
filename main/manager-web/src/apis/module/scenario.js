import { getServiceUrl } from '../api';
import RequestService from '../httpRequest';

export default {
    // ==================== 场景管理 API ====================
    
    // 获取场景列表
    getScenarioList(params, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario/list`)
            .method('GET')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);  // 统一传递完整响应
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getScenarioList(params, callback);
                });
            }).send();
    },
    
    // 获取场景详情
    getScenario(scenarioId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario/${scenarioId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);  // 统一传递完整响应
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getScenario(scenarioId, callback);
                });
            }).send();
    },
    
    // 保存场景
    saveScenario(scenarioData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario`)
            .method('POST')
            .data(scenarioData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);  // 统一传递完整响应
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.saveScenario(scenarioData, callback);
                });
            }).send();
    },
    
    // 更新场景
    updateScenario(scenarioId, scenarioData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario/${scenarioId}`)
            .method('PUT')
            .data(scenarioData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);  // 统一传递完整响应
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.updateScenario(scenarioId, scenarioData, callback);
                });
            }).send();
    },
    
    // 删除场景
    deleteScenario(scenarioId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario/${scenarioId}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);  // 统一传递完整响应
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.deleteScenario(scenarioId, callback);
                });
            }).send();
    },
    
    // 启用/禁用场景
    toggleScenario(scenarioId, isActive, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario/${scenarioId}/toggle`)
            .method('PUT')
            .data({ isActive: isActive })
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);  // 统一传递完整响应
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.toggleScenario(scenarioId, isActive, callback);
                });
            }).send();
    },
    
    // 根据智能体ID获取场景列表
    getScenariosByAgentId(agentId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario/agent/${agentId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getScenariosByAgentId(agentId, callback);
                });
            }).send();
    },
    
    // 根据场景类型获取活跃场景列表
    getActiveScenariosByType(scenarioType, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario/active/${scenarioType}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getActiveScenariosByType(scenarioType, callback);
                });
            }).send();
    },
    
    // ==================== 步骤管理 API ====================
    
    // 获取场景步骤列表
    getScenarioSteps(scenarioId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario-step/list/${scenarioId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getScenarioSteps(scenarioId, callback);
                });
            }).send();
    },
    
    // 批量保存场景步骤
    saveScenarioSteps(scenarioId, stepsData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario-step/batch-save/${scenarioId}`)
            .method('POST')
            .data(stepsData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.saveScenarioSteps(scenarioId, stepsData, callback);
                });
            }).send();
    },
    
    // 删除步骤
    deleteScenarioStep(stepId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario-step/${stepId}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.deleteScenarioStep(stepId, callback);
                });
            }).send();
    },
    
    // 获取场景步骤数量
    getScenarioStepCount(scenarioId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/scenario-step/count/${scenarioId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getScenarioStepCount(scenarioId, callback);
                });
            }).send();
    },
    
    // ==================== 模板管理 API ====================
    
    // 获取步骤模板列表
    getStepTemplateList(callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/step-template/list`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getStepTemplateList(callback);
                });
            }).send();
    },
    
    // 获取步骤模板详情
    getStepTemplate(templateId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/step-template/${templateId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getStepTemplate(templateId, callback);
                });
            }).send();
    },
    
    // 保存步骤模板
    saveStepTemplate(templateData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/step-template`)
            .method('POST')
            .data(templateData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.saveStepTemplate(templateData, callback);
                });
            }).send();
    },
    
    // 更新步骤模板
    updateStepTemplate(templateId, templateData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/step-template/${templateId}`)
            .method('PUT')
            .data(templateData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.updateStepTemplate(templateId, templateData, callback);
                });
            }).send();
    },
    
    // 删除步骤模板
    deleteStepTemplate(templateId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/step-template/${templateId}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.deleteStepTemplate(templateId, callback);
                });
            }).send();
    },
    
    // ==================== 学习记录管理 API ====================
    
    // 获取学习记录列表
    getLearningRecords(params, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/learning-record/list`)
            .method('GET')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getLearningRecords(params, callback);
                });
            }).send();
    },
    
    // 获取学习记录详情
    getLearningRecord(recordId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/learning-record/${recordId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getLearningRecord(recordId, callback);
                });
            }).send();
    },
    
    // 保存学习记录
    saveLearningRecord(recordData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/learning-record`)
            .method('POST')
            .data(recordData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.saveLearningRecord(recordData, callback);
                });
            }).send();
    },
    
    // 更新学习记录
    updateLearningRecord(recordId, recordData, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/learning-record/${recordId}`)
            .method('PUT')
            .data(recordData)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.updateLearningRecord(recordId, recordData, callback);
                });
            }).send();
    },
    
    // 删除学习记录
    deleteLearningRecord(recordId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/learning-record/${recordId}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.deleteLearningRecord(recordId, callback);
                });
            }).send();
    },
    
    // 根据智能体ID获取学习记录
    getLearningRecordsByAgentId(agentId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/learning-record/agent/${agentId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getLearningRecordsByAgentId(agentId, callback);
                });
            }).send();
    },
    
    // 根据场景ID获取学习记录
    getLearningRecordsByScenarioId(scenarioId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/learning-record/scenario/${scenarioId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getLearningRecordsByScenarioId(scenarioId, callback);
                });
            }).send();
    },
    
    // 根据儿童姓名获取学习记录
    getLearningRecordsByChildName(childName, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/learning-record/child/${childName}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getLearningRecordsByChildName(childName, callback);
                });
            }).send();
    },
    
    // 获取学习统计信息
    getLearningStatistics(agentId, childName, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/xiaozhi/learning-record/statistics`)
            .method('GET')
            .data({ agentId: agentId, childName: childName })
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.getLearningStatistics(agentId, childName, callback);
                });
            }).send();
    }
}