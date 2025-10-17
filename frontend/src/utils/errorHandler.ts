import safeMessage from './message';

export interface ErrorReport {
  message: string;
  stack?: string;
  timestamp: string;
  userAgent: string;
  url: string;
  userId?: string;
  sessionId?: string;
  additionalInfo?: Record<string, any>;
}

export class GlobalErrorHandler {
  private static instance: GlobalErrorHandler;
  private errorQueue: ErrorReport[] = [];
  private isReporting = false;
  private errorCount = 0;
  private lastErrorTime = 0;
  private readonly MAX_ERRORS_PER_MINUTE = 10;
  private readonly ERROR_RESET_INTERVAL = 60000; // 1分钟

  private constructor() {
    this.setupGlobalHandlers();
  }

  public static getInstance(): GlobalErrorHandler {
    if (!GlobalErrorHandler.instance) {
      GlobalErrorHandler.instance = new GlobalErrorHandler();
    }
    return GlobalErrorHandler.instance;
  }

  private setupGlobalHandlers() {
    // 捕获未处理的 JavaScript 错误
    window.addEventListener('error', (event) => {
      this.handleError(event.error || new Error(event.message), {
        type: 'javascript',
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      });
    });

    // 捕获未处理的 Promise 拒绝
    window.addEventListener('unhandledrejection', (event) => {
      this.handleError(
        event.reason instanceof Error ? event.reason : new Error(String(event.reason)),
        {
          type: 'promise',
          reason: event.reason
        }
      );
    });

    // 捕获资源加载错误
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.handleError(new Error(`Resource loading error: ${(event.target as any)?.src || 'unknown'}`), {
          type: 'resource',
          target: event.target
        });
      }
    }, true);
  }

  public handleError(error: Error, additionalInfo?: Record<string, any>) {
    // 防止错误循环 - 检查错误频率
    const now = Date.now();
    if (now - this.lastErrorTime > this.ERROR_RESET_INTERVAL) {
      this.errorCount = 0;
    }
    
    this.errorCount++;
    this.lastErrorTime = now;

    // 如果错误频率过高，跳过处理
    if (this.errorCount > this.MAX_ERRORS_PER_MINUTE) {
      console.warn('[ErrorHandler] Too many errors, skipping error handling to prevent infinite loop');
      return;
    }

    // 特殊处理：如果是notification相关错误或Cytoscape错误，不显示用户消息避免循环
    const isNotificationError = error.message.includes('notify') || 
                               error.message.includes('notification') || 
                               error.message.includes('Cannot read properties of null');
    
    const isCytoscapeError = error.message.includes('cytoscape') ||
                            error.stack?.includes('cytoscape') ||
                            additionalInfo?.filename?.includes('cytoscape');

    const errorReport: ErrorReport = {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      additionalInfo
    };

    // 添加用户和会话信息（如果可用）
    try {
      const userId = localStorage.getItem('userId');
      const sessionId = sessionStorage.getItem('sessionId');
      if (userId) errorReport.userId = userId;
      if (sessionId) errorReport.sessionId = sessionId;
    } catch (e) {
      // 忽略存储访问错误
    }

    // 记录到控制台
    console.error('Global error handler:', error, additionalInfo);

    // 添加到队列
    this.errorQueue.push(errorReport);

    // 只有非通知错误和非Cytoscape错误才显示用户消息
    if (!isNotificationError && !isCytoscapeError) {
      this.showUserMessage(error, additionalInfo);
    } else if (isCytoscapeError) {
      // Cytoscape错误只记录到控制台，不显示用户消息
      console.warn('[Cytoscape Error] Graph visualization error occurred:', error.message);
    }

    // 异步报告错误
    this.reportErrors();
  }

  private showUserMessage(error: Error, additionalInfo?: Record<string, any>) {
    // 使用安全的消息函数
    try {
      if (additionalInfo?.type === 'network') {
        safeMessage.error('网络连接出现问题，请检查您的网络连接');
      } else if (additionalInfo?.type === 'resource') {
        safeMessage.warning('某些资源加载失败，页面可能无法正常显示');
      } else if (error.message.includes('ChunkLoadError')) {
        safeMessage.error('应用程序更新了，请刷新页面重新加载');
      } else {
        safeMessage.error('应用程序遇到错误，我们已经记录了这个问题');
      }
    } catch (e) {
      // 如果message调用失败，使用console作为fallback
      console.warn('Failed to show user message:', error.message);
    }
  }

  private async reportErrors() {
    if (this.isReporting || this.errorQueue.length === 0) {
      return;
    }

    this.isReporting = true;

    try {
      const errors = [...this.errorQueue];
      this.errorQueue = [];

      // 发送错误报告到服务器
      await this.sendErrorReport(errors);
    } catch (reportError) {
      console.warn('Failed to report errors:', reportError);
      // 不要重新加入队列，避免无限循环
      // 错误已经记录到控制台和本地存储
    } finally {
      this.isReporting = false;
    }
  }

  private async sendErrorReport(errors: ErrorReport[]): Promise<void> {
    // 这里实现发送错误报告到服务器的逻辑
    // 可以集成 Sentry, LogRocket 或自定义错误报告服务
    
    try {
      const response = await fetch('/api/v1/errors/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ errors }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      // 如果服务器不可用，至少记录到本地存储
      this.saveToLocalStorage(errors);
      // 重新抛出错误，但在reportErrors中不会触发新的错误处理
      throw error;
      throw error;
    }
  }

  private saveToLocalStorage(errors: ErrorReport[]) {
    try {
      const existingErrors = JSON.parse(localStorage.getItem('errorReports') || '[]');
      const allErrors = [...existingErrors, ...errors];
      
      // 只保留最近的 50 个错误报告
      const recentErrors = allErrors.slice(-50);
      
      localStorage.setItem('errorReports', JSON.stringify(recentErrors));
    } catch (e) {
      console.error('Failed to save errors to localStorage:', e);
    }
  }

  public getStoredErrors(): ErrorReport[] {
    try {
      return JSON.parse(localStorage.getItem('errorReports') || '[]');
    } catch (e) {
      return [];
    }
  }

  public clearStoredErrors() {
    try {
      localStorage.removeItem('errorReports');
    } catch (e) {
      console.error('Failed to clear stored errors:', e);
    }
  }

  // 手动报告错误的方法
  public reportError(error: Error | string, additionalInfo?: Record<string, any>) {
    const errorObj = typeof error === 'string' ? new Error(error) : error;
    this.handleError(errorObj, additionalInfo);
  }

  // 网络错误处理
  public handleNetworkError(error: Error, request?: any) {
    this.handleError(error, {
      type: 'network',
      request: {
        url: request?.url,
        method: request?.method,
        status: request?.status
      }
    });
  }

  // API 错误处理
  public handleApiError(error: Error, endpoint: string, method: string, status?: number) {
    this.handleError(error, {
      type: 'api',
      endpoint,
      method,
      status
    });
  }
}

// 导出单例实例
export const globalErrorHandler = GlobalErrorHandler.getInstance();

// 便捷函数
export const reportError = (error: Error | string, additionalInfo?: Record<string, any>) => {
  globalErrorHandler.reportError(error, additionalInfo);
};

export const reportNetworkError = (error: Error, request?: any) => {
  globalErrorHandler.handleNetworkError(error, request);
};

export const reportApiError = (error: Error, endpoint: string, method: string, status?: number) => {
  globalErrorHandler.handleApiError(error, endpoint, method, status);
};