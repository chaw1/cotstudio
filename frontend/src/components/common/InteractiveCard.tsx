import React from 'react';
import { Card, CardProps } from 'antd';

interface InteractiveCardProps extends Omit<CardProps, 'variant'> {
  interactive?: boolean;
  elevation?: 'none' | 'sm' | 'md' | 'lg';
  hoverEffect?: 'lift' | 'scale' | 'glow' | 'none';
  clickable?: boolean;
  selected?: boolean;
  variant?: 'default' | 'outlined' | 'filled' | 'glass';
}

/**
 * InteractiveCard - 增强的交互式卡片组件
 * 
 * 功能特性：
 * - 多种悬停效果
 * - 可配置的阴影层级
 * - 选中状态支持
 * - 玻璃态效果
 * - 无障碍优化
 */
const InteractiveCard: React.FC<InteractiveCardProps> = ({
  interactive = true,
  elevation = 'sm',
  hoverEffect = 'lift',
  clickable = false,
  selected = false,
  variant = 'default',
  className = '',
  style = {},
  children,
  onClick,
  ...props
}) => {
  const getCardClassName = () => {
    const classes = ['enhanced-card'];
    
    if (interactive && hoverEffect !== 'none') {
      classes.push(`hover-${hoverEffect}`);
    }
    
    if (clickable) {
      classes.push('clickable-card');
    }
    
    if (selected) {
      classes.push('selected-card');
    }
    
    if (elevation !== 'none') {
      classes.push(`shadow-${elevation}`);
    }
    
    classes.push(`card-${variant}`);
    classes.push(className);
    
    return classes.join(' ');
  };

  const getCardStyle = (): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      borderRadius: '12px',
      transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
      cursor: clickable ? 'pointer' : 'default',
      ...style,
    };

    // 根据变体设置样式
    switch (variant) {
      case 'outlined':
        return {
          ...baseStyle,
          border: '2px solid #f0f0f0',
          background: '#ffffff',
        };
      case 'filled':
        return {
          ...baseStyle,
          background: '#fafafa',
          border: 'none',
        };
      case 'glass':
        return {
          ...baseStyle,
          background: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
        };
      default:
        return baseStyle;
    }
  };

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (clickable && onClick) {
      onClick(e);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (clickable && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      if (onClick) {
        onClick(e as any);
      }
    }
  };

  return (
    <Card
      {...props}
      className={getCardClassName()}
      style={getCardStyle()}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={clickable ? 0 : undefined}
      role={clickable ? 'button' : undefined}
      aria-pressed={clickable && selected ? true : undefined}
    >
      {children}
      
      {/* 添加自定义样式 */}
      <style>{`
        .enhanced-card {
          position: relative;
          overflow: hidden;
        }
        
        .enhanced-card.hover-lift:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 25px 0 rgba(0, 0, 0, 0.1);
        }
        
        .enhanced-card.hover-scale:hover {
          transform: scale(1.02);
        }
        
        .enhanced-card.hover-glow:hover {
          box-shadow: 0 0 20px rgba(22, 119, 255, 0.3);
        }
        
        .enhanced-card.clickable-card {
          cursor: pointer;
        }
        
        .enhanced-card.clickable-card:active {
          transform: scale(0.98);
        }
        
        .enhanced-card.selected-card {
          border-color: #1677ff;
          box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.2);
        }
        
        .enhanced-card.card-outlined:hover {
          border-color: #1677ff;
        }
        
        .enhanced-card.card-filled:hover {
          background: #f0f0f0;
        }
        
        .enhanced-card:focus-visible {
          outline: 2px solid #1677ff;
          outline-offset: 2px;
        }
        
        /* 加载状态 */
        .enhanced-card.loading {
          pointer-events: none;
          opacity: 0.7;
        }
        
        .enhanced-card.loading::after {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(90deg, transparent 25%, rgba(255, 255, 255, 0.5) 50%, transparent 75%);
          background-size: 200% 100%;
          animation: shimmer 1.5s infinite;
        }
        
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </Card>
  );
};

export default InteractiveCard;