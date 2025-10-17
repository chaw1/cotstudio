import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Typography, Card, Space, Alert } from 'antd';
import { ReloadOutlined, BugOutlined, HomeOutlined } from '@ant-design/icons';

const { Paragraph, Text } = Typography;

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // 调用自定义错误处理函数
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // 记录错误到控制台
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // 可以在这里添加错误报告逻辑
    this.reportError(error, errorInfo);
  }

  reportError = (error: Error, errorInfo: ErrorInfo) => {
    // 这里可以集成错误报告服务，如 Sentry, LogRocket 等
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    // 发送错误报告到服务器
    try {
      // 这里可以调用 API 发送错误报告
      console.log('Error report:', errorReport);
    } catch (reportError) {
      console.error('Failed to report error:', reportError);
    }
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      // 如果提供了自定义 fallback，使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认错误界面
      return (
        <div style={{ 
          padding: '24px', 
          minHeight: '100vh', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          backgroundColor: '#f5f5f5'
        }}>
          <Card style={{ maxWidth: '600px', width: '100%' }}>
            <Result
              status="error"
              icon={<BugOutlined style={{ color: '#ff4d4f' }} />}
              title="应用程序遇到错误"
              subTitle="很抱歉，应用程序遇到了一个意外错误。我们已经记录了这个问题。"
              extra={
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Space>
                    <Button type="primary" icon={<ReloadOutlined />} onClick={this.handleReload}>
                      重新加载页面
                    </Button>
                    <Button icon={<HomeOutlined />} onClick={this.handleGoHome}>
                      返回首页
                    </Button>
                    <Button onClick={this.handleReset}>
                      重试
                    </Button>
                  </Space>
                </Space>
              }
            />

            {/* 开发环境下显示详细错误信息 */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Card 
                title="错误详情 (仅开发环境显示)" 
                style={{ marginTop: '16px' }}
                size="small"
              >
                <Alert
                  message="错误信息"
                  description={
                    <div>
                      <Paragraph>
                        <Text strong>错误:</Text> {this.state.error.message}
                      </Paragraph>
                      {this.state.error.stack && (
                        <Paragraph>
                          <Text strong>堆栈跟踪:</Text>
                          <pre style={{ 
                            fontSize: '12px', 
                            backgroundColor: '#f5f5f5', 
                            padding: '8px', 
                            borderRadius: '4px',
                            overflow: 'auto',
                            maxHeight: '200px'
                          }}>
                            {this.state.error.stack}
                          </pre>
                        </Paragraph>
                      )}
                      {this.state.errorInfo?.componentStack && (
                        <Paragraph>
                          <Text strong>组件堆栈:</Text>
                          <pre style={{ 
                            fontSize: '12px', 
                            backgroundColor: '#f5f5f5', 
                            padding: '8px', 
                            borderRadius: '4px',
                            overflow: 'auto',
                            maxHeight: '200px'
                          }}>
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </Paragraph>
                      )}
                    </div>
                  }
                  type="error"
                  showIcon
                />
              </Card>
            )}
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

// 高阶组件版本，用于包装其他组件
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode,
  onError?: (error: Error, errorInfo: ErrorInfo) => void
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={fallback} onError={onError}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};

// Hook 版本，用于函数组件中的错误处理
export const useErrorHandler = () => {
  const handleError = React.useCallback((error: Error, errorInfo?: any) => {
    console.error('Error caught by useErrorHandler:', error, errorInfo);
    
    // 这里可以添加错误报告逻辑
    const errorReport = {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      ...errorInfo
    };

    // 发送错误报告
    try {
      console.log('Error report:', errorReport);
    } catch (reportError) {
      console.error('Failed to report error:', reportError);
    }
  }, []);

  return { handleError };
};