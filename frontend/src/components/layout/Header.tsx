import React from 'react';
import { Layout, Button, Typography, Space, Breadcrumb } from 'antd';
import { 
  MenuFoldOutlined, 
  MenuUnfoldOutlined,
  HomeOutlined
} from '@ant-design/icons';
import { useLocation } from 'react-router-dom';

const { Header: AntHeader } = Layout;
const { Title } = Typography;

interface HeaderProps {
  collapsed: boolean;
  onToggle: () => void;
  breakpoint?: string;
  isMobile?: boolean;
  isTablet?: boolean;
  isDesktop?: boolean;
}

const Header: React.FC<HeaderProps> = ({ 
  collapsed, 
  onToggle, 
  breakpoint = 'lg',
  isMobile = false,
  isTablet = false,
  isDesktop = true
}) => {
  const location = useLocation();

  // 响应式配置
  const logoSize = isMobile ? 24 : 32;
  const buttonSize = isMobile ? 36 : 40;
  const avatarSize = isMobile ? 24 : 28;
  const spaceSize = isMobile ? 'small' : 'middle';
  const showTitle = !isMobile || !collapsed;

  // 页面路径映射
  const pathMap: Record<string, string> = {
    '/dashboard': '仪表板',
    '/projects': '项目管理',
    '/annotation': 'CoT标注',
    '/knowledge-graph': '知识图谱',
    '/export': '数据导出',
    '/user-management': '用户管理',
    '/settings': '系统设置',
  };

  // 获取当前页面标题
  const getCurrentPageTitle = () => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    if (pathSegments.length > 0) {
      const currentPath = `/${pathSegments[0]}`;
      return pathMap[currentPath] || 'COT Studio';
    }
    return 'COT Studio';
  };

  // 生成面包屑导航
  const getBreadcrumbs = () => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    const breadcrumbs = [
      {
        title: <HomeOutlined />,
        href: '/dashboard',
      }
    ];

    if (pathSegments.length > 0) {
      const currentPath = `/${pathSegments[0]}`;
      if (pathMap[currentPath]) {
        breadcrumbs.push({
          title: <span>{pathMap[currentPath]}</span>,
          href: currentPath,
        });
      }
    }

    return breadcrumbs;
  };

  const headerPadding = isMobile ? '0 12px' : '0 24px';

  return (
    <AntHeader
      style={{
        padding: headerPadding,
        background: 'var(--color-bg-container)',
        borderBottom: '1px solid var(--color-border-secondary)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: 'var(--header-height)',
        position: 'relative',
        zIndex: 'var(--z-index-header)',
      }}
    >
      <Space align="center" size={isMobile ? 'small' : 'large'}>
        {/* 折叠按钮 */}
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={onToggle}
          style={{
            fontSize: isMobile ? '14px' : '16px',
            width: buttonSize,
            height: buttonSize,
            borderRadius: 'var(--border-radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          className="modern-button"
        />

        {/* Logo和标题 - 在移动端可能隐藏标题 */}
        {showTitle && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
            <Title
              level={4}
              style={{
                margin: 0,
                color: 'var(--color-text-primary)',
                fontSize: 'var(--font-size-xl)',
                fontWeight: 'var(--font-weight-semibold)',
                lineHeight: 'var(--line-height-tight)'
              }}
            >
              {getCurrentPageTitle()}
            </Title>
            
            <Breadcrumb
              items={getBreadcrumbs()}
              style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-secondary)',
                marginTop: 'var(--spacing-xs)'
              }}
            />
          </div>
        )}
      </Space>

      {/* 右侧可以添加搜索框或其他工具 */}
      <Space size="middle" align="center">
        <div style={{
          display: isMobile ? 'none' : 'block',
          color: 'var(--color-text-secondary)',
          fontSize: 'var(--font-size-sm)'
        }}>
          欢迎使用 COT Studio
        </div>
      </Space>
    </AntHeader>
  );
};

export default Header;