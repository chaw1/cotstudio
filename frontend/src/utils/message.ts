import { message as antdMessage, App } from 'antd';

// 创建一个安全的消息实例，在React上下文外也能使用
let messageInstance = antdMessage;
let isMessageAvailable = false;
let appInstance: any = null;

// 设置App实例的函数（将在组件中调用）
export const setAppInstance = (app: any) => {
  appInstance = app;
  if (app && app.message) {
    messageInstance = app.message;
    checkMessageAvailability();
  }
};

// 检查消息实例是否可用
const checkMessageAvailability = () => {
  try {
    // 优先使用App实例中的message
    if (appInstance && appInstance.message) {
      messageInstance = appInstance.message;
    }
    
    // 检查消息实例是否存在和可用
    if (messageInstance && 
        typeof messageInstance === 'object' && 
        typeof messageInstance.success === 'function' &&
        typeof messageInstance.error === 'function' &&
        typeof messageInstance.warning === 'function' &&
        typeof messageInstance.info === 'function') {
      isMessageAvailable = true;
      return true;
    }
  } catch (error) {
    console.warn('[SafeMessage] Message instance not ready:', error?.message || error);
  }
  isMessageAvailable = false;
  return false;
};

// 初始检查
setTimeout(() => checkMessageAvailability(), 100);

// 安全的消息函数
const safeMessage = {
  success: (content: string) => {
    try {
      if (!isMessageAvailable) {
        checkMessageAvailability();
      }
      
      if (isMessageAvailable && messageInstance && messageInstance.success) {
        messageInstance.success(content);
      } else {
        console.log(`SUCCESS: ${content}`);
      }
    } catch (error) {
      console.log(`SUCCESS: ${content}`);
      console.warn('[SafeMessage] Failed to show success message:', error?.message || error);
    }
  },
  error: (content: string) => {
    try {
      if (!isMessageAvailable) {
        checkMessageAvailability();
      }
      
      if (isMessageAvailable && messageInstance && messageInstance.error) {
        messageInstance.error(content);
      } else {
        console.error(`ERROR: ${content}`);
      }
    } catch (error) {
      console.error(`ERROR: ${content}`);
      console.warn('[SafeMessage] Failed to show error message:', error?.message || error);
    }
  },
  warning: (content: string) => {
    try {
      if (!isMessageAvailable) {
        checkMessageAvailability();
      }
      
      if (isMessageAvailable && messageInstance && messageInstance.warning) {
        messageInstance.warning(content);
      } else {
        console.warn(`WARNING: ${content}`);
      }
    } catch (error) {
      console.warn(`WARNING: ${content}`);
      console.warn('[SafeMessage] Failed to show warning message:', error?.message || error);
    }
  },
  info: (content: string) => {
    try {
      if (!isMessageAvailable) {
        checkMessageAvailability();
      }
      
      if (isMessageAvailable && messageInstance && messageInstance.info) {
        messageInstance.info(content);
      } else {
        console.info(`INFO: ${content}`);
      }
    } catch (error) {
      console.info(`INFO: ${content}`);
      console.warn('[SafeMessage] Failed to show info message:', error?.message || error);
    }
  },
  loading: (content: string) => {
    try {
      if (!isMessageAvailable) {
        checkMessageAvailability();
      }
      
      if (isMessageAvailable && messageInstance && messageInstance.loading) {
        return messageInstance.loading(content);
      } else {
        console.log(`LOADING: ${content}`);
        return () => {}; // 返回一个空的销毁函数
      }
    } catch (error) {
      console.log(`LOADING: ${content}`);
      console.warn('[SafeMessage] Failed to show loading message:', error?.message || error);
      return () => {}; // 返回一个空的销毁函数
    }
  }
};

export default safeMessage;
