import React from 'react';
import { Button, ButtonProps } from 'antd';

interface EnhancedButtonProps extends Omit<ButtonProps, 'variant'> {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'ghost' | 'text';
  interactive?: boolean;
  elevation?: 'none' | 'sm' | 'md' | 'lg';
  rounded?: boolean;
}

/**
 * EnhancedButton - 增强的按钮组件
 * 
 * 功能特性：
 * - 现代化视觉设计
 * - 丰富的交互效果
 * - 可配置的阴影和圆角
 * - 无障碍优化
 * - 响应式适配
 */
const EnhancedButton: React.FC<EnhancedButtonProps> = ({
  variant = 'secondary',
  interactive = true,
  elevation = 'sm',
  rounded = false,
  className = '',
  style = {},
  children,
  ...props
}) => {
  // 计算按钮样式类名
  const getButtonClassName = () => {
    const classes = ['enhanced-button'];
    
    if (interactive) {
      classes.push('interactive-scale');
    }
    
    if (elevation !== 'none') {
      classes.push(`shadow-${elevation}`);
    }
    
    if (rounded) {
      classes.push('rounded-full');
    }
    
    classes.push(className);
    
    return classes.join(' ');
  };

  // 计算按钮类型
  const getButtonType = (): ButtonProps['type'] => {
    switch (variant) {
      case 'primary':
        return 'primary';
      case 'danger':
        return 'primary';
      case 'ghost':
        return 'default';
      case 'text':
        return 'text';
      default:
        return 'default';
    }
  };

  // 计算按钮样式
  const getButtonStyle = () => {
    const baseStyle: React.CSSProperties = {
      fontWeight: 500,
      transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
      border: 'none',
      ...style,
    };

    switch (variant) {
      case 'success':
        return {
          ...baseStyle,
          background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
          color: '#ffffff',
          boxShadow: '0 2px 4px 0 rgba(82, 196, 26, 0.2)',
        };
      case 'warning':
        return {
          ...baseStyle,
          background: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)',
          color: '#ffffff',
          boxShadow: '0 2px 4px 0 rgba(250, 173, 20, 0.2)',
        };
      case 'danger':
        return {
          ...baseStyle,
          background: 'linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%)',
          color: '#ffffff',
          boxShadow: '0 2px 4px 0 rgba(255, 77, 79, 0.2)',
        };
      case 'ghost':
        return {
          ...baseStyle,
          background: 'transparent',
          border: '1px solid #1677ff',
          color: '#1677ff',
        };
      default:
        return baseStyle;
    }
  };

  return (
    <Button
      {...props}
      type={getButtonType()}
      className={getButtonClassName()}
      style={getButtonStyle()}
      danger={variant === 'danger'}
    >
      {children}
    </Button>
  );
};

export default EnhancedButton;