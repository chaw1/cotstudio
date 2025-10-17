import React from 'react';
import { Typography, Space, Button, Breadcrumb } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useResponsiveBreakpoint } from '../../hooks/useResponsiveBreakpoint';

const { Title, Text } = Typography;

interface BreadcrumbItem {
  title: string;
  icon?: React.ReactNode;
  onClick?: () => void;
}

interface ResponsivePageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode[];
  onBack?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * 响应式页面头部组件
 */
const ResponsivePageHeader: React.FC<ResponsivePageHeaderProps> = ({
  title,
  subtitle,
  icon,
  breadcrumbs = [],
  actions = [],
  onBack,
  className = '',
  style = {}
}) => {
  const { isMobile, isTablet, breakpoint } = useResponsiveBreakpoint();

  // 响应式样式计算
  const titleLevel = isMobile ? 3 : 2;
  const spacing = isMobile ? 'small' : 'middle';
  const buttonSize = isMobile ? 'small' : 'middle';

  return (
    <div 
      className={`responsive-page-header ${className}`}
      style={{
        marginBottom: isMobile ? '16px' : '24px',
        ...style
      }}
    >
      {/* 面包屑导航 - 在移动端可能隐藏 */}
      {breadcrumbs.length > 0 && !isMobile && (
        <Breadcrumb style={{ marginBottom: '16px' }}>
          {breadcrumbs.map((item, index) => (
            <Breadcrumb.Item key={index}>
              {item.onClick ? (
                <Button 
                  type="link" 
                  icon={item.icon}
                  onClick={item.onClick}
                  style={{ padding: 0, fontSize: '12px' }}
                >
                  {item.title}
                </Button>
              ) : (
                <span>{item.title}</span>
              )}
            </Breadcrumb.Item>
          ))}
        </Breadcrumb>
      )}

      {/* 标题和操作区域 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: isMobile ? 'flex-start' : 'center',
        flexDirection: isMobile ? 'column' : 'row',
        gap: isMobile ? '12px' : '16px'
      }}>
        {/* 标题区域 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* 返回按钮 - 移动端显示 */}
            {onBack && isMobile && (
              <Button
                type="text"
                icon={<ArrowLeftOutlined />}
                onClick={onBack}
                size={buttonSize}
                style={{ padding: '4px' }}
              />
            )}
            
            <Title 
              level={titleLevel} 
              style={{ 
                margin: 0,
                fontSize: isMobile ? '18px' : undefined,
                lineHeight: 1.2,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: isMobile ? 'nowrap' : 'normal'
              }}
            >
              <Space size={spacing}>
                {icon && (
                  <span style={{ fontSize: isMobile ? '16px' : '20px' }}>
                    {icon}
                  </span>
                )}
                <span>{title}</span>
              </Space>
            </Title>
          </div>
          
          {subtitle && (
            <Text 
              type="secondary" 
              style={{ 
                display: 'block', 
                marginTop: '4px',
                fontSize: isMobile ? '12px' : '14px',
                lineHeight: 1.4,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: isMobile ? 'nowrap' : 'normal'
              }}
            >
              {subtitle}
            </Text>
          )}
        </div>

        {/* 操作按钮区域 */}
        {actions.length > 0 && (
          <div style={{
            display: 'flex',
            gap: isMobile ? '8px' : '12px',
            flexWrap: isMobile ? 'wrap' : 'nowrap',
            width: isMobile ? '100%' : 'auto'
          }}>
            {/* 返回按钮 - 桌面端显示 */}
            {onBack && !isMobile && (
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={onBack}
                size={buttonSize}
              >
                返回
              </Button>
            )}
            
            {actions.map((action, index) => (
              <div 
                key={index}
                style={{ 
                  flex: isMobile ? '1' : 'none',
                  minWidth: isMobile ? '0' : 'auto'
                }}
              >
                {React.cloneElement(action as React.ReactElement, {
                  size: buttonSize,
                  style: {
                    width: isMobile ? '100%' : 'auto',
                    ...(action as React.ReactElement).props?.style
                  }
                })}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ResponsivePageHeader;