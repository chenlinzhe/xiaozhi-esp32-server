/**
 * API响应数据处理工具
 * 统一处理后端返回的嵌套数据结构
 */

/**
 * 提取业务数据
 * @param {Object} response - HTTP响应对象
 * @returns {Object} 业务数据对象
 */
export function extractBusinessData(response) {
  if (!response) {
    return null;
  }
  
  // 如果response本身就是业务数据（code字段存在）
  if (response.code !== undefined) {
    return response;
  }
  
  // 如果response是HTTP响应对象，业务数据在data字段中
  if (response.data && response.data.code !== undefined) {
    return response.data;
  }
  
  // 如果都不符合，返回原始数据
  return response;
}

/**
 * 检查API调用是否成功
 * @param {Object} response - HTTP响应对象
 * @returns {boolean} 是否成功
 */
export function isApiSuccess(response) {
  const businessData = extractBusinessData(response);
  return businessData && businessData.code === 0;
}

/**
 * 获取错误信息
 * @param {Object} response - HTTP响应对象
 * @param {string} defaultMsg - 默认错误信息
 * @returns {string} 错误信息
 */
export function getErrorMessage(response, defaultMsg = '请求失败') {
  const businessData = extractBusinessData(response);
  return businessData ? (businessData.msg || defaultMsg) : defaultMsg;
}

/**
 * 获取业务数据
 * @param {Object} response - HTTP响应对象
 * @returns {*} 业务数据
 */
export function getBusinessData(response) {
  const businessData = extractBusinessData(response);
  return businessData ? businessData.data : null;
}

/**
 * 创建统一的API回调处理函数
 * @param {Function} successCallback - 成功回调
 * @param {Function} errorCallback - 错误回调
 * @param {string} defaultErrorMsg - 默认错误信息
 * @returns {Function} 统一的回调处理函数
 */
export function createApiCallback(successCallback, errorCallback, defaultErrorMsg = '请求失败') {
  return (response) => {
    if (isApiSuccess(response)) {
      const data = getBusinessData(response);
      if (successCallback) {
        successCallback(data, response);
      }
    } else {
      const errorMsg = getErrorMessage(response, defaultErrorMsg);
      if (errorCallback) {
        errorCallback(errorMsg, response);
      }
    }
  };
}

/**
 * 创建Promise包装的API调用
 * @param {Function} apiCall - API调用函数
 * @param {Array} args - API调用参数
 * @returns {Promise} Promise对象
 */
export function createApiPromise(apiCall, ...args) {
  return new Promise((resolve, reject) => {
    apiCall(...args, (response) => {
      if (isApiSuccess(response)) {
        const data = getBusinessData(response);
        resolve(data);
      } else {
        const errorMsg = getErrorMessage(response);
        reject(new Error(errorMsg));
      }
    });
  });
}

/**
 * 日志记录工具
 */
export const ApiLogger = {
  log: (message, data) => {
    console.log(`[API] ${message}`, data);
  },
  
  error: (message, data) => {
    console.error(`[API Error] ${message}`, data);
  },
  
  warn: (message, data) => {
    console.warn(`[API Warning] ${message}`, data);
  }
};

export default {
  extractBusinessData,
  isApiSuccess,
  getErrorMessage,
  getBusinessData,
  createApiCallback,
  createApiPromise,
  ApiLogger
};
