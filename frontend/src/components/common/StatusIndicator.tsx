import React from 'react';
import { Badge, Tag, Tooltip } from 'antd';
import { 
  CheckCircleOutlined, 
  ExclamationCircleOutlined, 
  CloseCircleOutlined, 
  ClockCircleOutlined,
  LoadingOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';

export type StatusType = 'success' | 'warning' | 'error' | 'info' | 'processing' | 'pending' | 'offline';

interface StatusIndicatorProps {
  status: StatusType;
  text?: string;
  tooltip?: string;
  size?: 'small' | 'default' | 'large';
  variant?: 'dot' | 'badge' | 'tag' | 'icon';
  animated?: boolean;
  showIcon?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * StatusIndicator - 状态指示器组件
 * 
 * 功能特性：
 * - 多种状态类型支持
 * - 丰富的视觉变体
 * - 动画效果
 * - 工具提示支持
 * - 无障碍优化
 */
const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  text,
  tooltip,
  size = 'default',
  variant = 'tag',
  animated = false,
  showIcon = true,
  className = '',
  style = {},
}) => {
  // 获取状态配置
  const getStatusConfig = () => {
    const configs = {
      success: {
        color: '#52c41a',
        bgColor: 'rgba(82, 196, 26, 0.1)',
        borderColor: 'rgba(82, 196, 26, 0.3)',
        icon: <CheckCircleOutlined />,
        label: '成功',
        antdStatus: 'success' as const,
      },
      warning: {
        color: '#faad14',
        bgColor: 'rgba(250, 173, 20, 0.1)',
        borderColor: 'rgba(250, 173, 20, 0.3)',
        icon: <ExclamationCircleOutlined />,
        label: '警告',
        antdStatus: 'warning' as const,
      },
      error: {
        color: '#ff4d4f',
        bgColor: 'rgba(255, 77, 79, 0.1)',
        borderColor: 'rgba(255, 77, 79, 0.3)',
        icon: <CloseCircleOutlined />,
        label: '错误',
        antdStatus: 'error' as const,
      },
      info: {
        color: '#1677ff',
        bgColor: 'rgba(22, 119, 255, 0.1)',
        borderColor: 'rgba(22, 119, 255, 0.3)',
        icon: <InfoCircleOutlined />,
        label: '信息',
        antdStatus: 'default' as const,
      },
      processing: {
        color: '#1677ff',
        bgColor: 'rgba(22, 119, 255, 0.1)',
        borderColor: 'rgba(22, 119, 255, 0.3)',
        icon: <LoadingOutlined spin />,
        label: '处理中',
        antdStatus: 'processing' as const,
      },
      pending: {
        color: '#8c8c8c',
        bgColor: 'rgba(140, 140, 140, 0.1)',
        borderColor: 'rgba(140, 140, 140, 0.3)',
        icon: <ClockCircleOutlined />,
        label: '等待中',
        antdStatus: 'default' as const,
      },
      offline: {
        color: '#bfbfbf',
        bgColor: 'rgba(191, 191, 191, 0.1)',
        borderColor: 'rgba(191, 191, 191, 0.3)',
        icon: <CloseCircleOutlined />,
        label: '离线',
        antdStatus: 'default' as const,
      },
    };

    return configs[status];
  };

  const config = getStatusConfig();
  const displayText = text || config.label;

  // 获取尺寸配置
  const getSizeConfig = () => {
    const sizes = {
      small: {
        fontSize: '12px',
        padding: '2px 6px',
        iconSize: '12px',
        dotSize: '6px',
      },
      default: {
        fontSize: '14px',
        padding: '4px 8px',
        iconSize: '14px',
        dotSize: '8px',
      },
      large: {
        fontSize: '16px',
        padding: '6px 12px',
        iconSize: '16px',
        dotSize: '10px',
      },
    };

    return sizes[size];
  };

  const sizeConfig = getSizeConfig();

  // 渲染不同变体
  const renderIndicator = () => {
    const baseClassName = `status-indicator status-${status} ${animated ? 'animated' : ''} ${className}`;
    
    switch (variant) {
      case 'dot':
        return (
          <span
            className={`${baseClassName} status-dot`}
            style={{
              display: 'inline-block',
              width: sizeConfig.dotSize,
              height: sizeConfig.dotSize,
              borderRadius: '50%',
              backgroundColor: config.color,
              animation: animated ? 'pulse 2s infinite' : 'none',
              ...style,
            }}
            aria-label={displayText}
          />
        );

      case 'badge':
        return (
          <Badge
            status={config.antdStatus}
            text={displayText}
            className={baseClassName}
            style={style}
          />
        );

      case 'icon':
        return (
          <span
            className={`${baseClassName} status-icon`}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              color: config.color,
              fontSize: sizeConfig.fontSize,
              ...style,
            }}
          >
            {showIcon && (
              <span style={{ fontSize: sizeConfig.iconSize }}>
                {config.icon}
              </span>
            )}
            {text && <span>{text}</span>}
          </span>
        );

      case 'tag':
      default:
        return (
          <Tag
            className={`${baseClassName} status-tag`}
            style={{
              color: config.color,
              backgroundColor: config.bgColor,
              border: `1px solid ${config.borderColor}`,
              borderRadius: '6px',
              fontSize: sizeConfig.fontSize,
              padding: sizeConfig.padding,
              margin: 0,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontWeight: 500,
              ...style,
            }}
          >
            {showIcon && (
              <span style={{ fontSize: sizeConfig.iconSize }}>
                {config.icon}
              </span>
            )}
            {displayText}
          </Tag>
        );
    }
  };

  const indicator = renderIndicator();

  // 如果有工具提示，包装在 Tooltip 中
  if (tooltip) {
    return (
      <Tooltip title={tooltip} placement="top">
        {indicator}
      </Tooltip>
    );
  }

  return (
    <>
      {indicator}
      
      {/* 添加动画样式 */}
      <style>{`
        @keyframes pulse {
          0% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.7;
            transform: scale(1.1);
          }
          100% {
            opacity: 1;
            transform: scale(1);
          }
        }
        
        @keyframes breathe {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.6;
          }
        }
        
        .status-indicator.animated.status-processing {
          animation: breathe 2s ease-in-out infinite;
        }
        
        .status-indicator.animated.status-pending {
          animation: pulse 2s ease-in-out infinite;
        }
        
        .status-indicator:focus-visible {
          outline: 2px solid #1677ff;
          outline-offset: 2px;
          border-radius: 4px;
        }
        
        /* 高对比度模式支持 */
        @media (prefers-contrast: high) {
          .status-tag {
            border-width: 2px !important;
          }
        }
        
        /* 减少动画模式支持 */
        @media (prefers-reduced-motion: reduce) {
          .status-indicator.animated {
            animation: none !important;
          }
        }
      `}</style>
    </>
  );
};

// 预设状态组件
export const SuccessIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator {...props} status="success" />
);

export const WarningIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator {...props} status="warning" />
);

export const ErrorIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator {...props} status="error" />
);

export const InfoIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator {...props} status="info" />
);

export const ProcessingIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator {...props} status="processing" animated />
);

export const PendingIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator {...props} status="pending" />
);

export const OfflineIndicator: React.FC<Omit<StatusIndicatorProps, 'status'>> = (props) => (
  <StatusIndicator {...props} status="offline" />
);

export default StatusIndicator;