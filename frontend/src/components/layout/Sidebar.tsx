import React, { useEffect, useRef } from 'react';
import { Menu, Avatar, Typography, Space, Button, Dropdown, Badge, Divider } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  ProjectOutlined,
  FileTextOutlined,
  BranchesOutlined,
  ExportOutlined,
  SettingOutlined,
  TeamOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { authService } from '../../services/authService';
import { useAccessibility, ScreenReaderOnly } from '../../hooks/useAccessibility';
import '../../styles/accessibility.css';

const { Text } = Typography;

interface SidebarProps {
  collapsed: boolean;
  breakpoint?: string;
  isMobile?: boolean;
  onMobileClose?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  collapsed, 
  breakpoint = 'lg',
  isMobile = false,
  onMobileClose
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { useKeyboardNavigation, announceToScreenReader, generateId } = useAccessibility();
  const sidebarRef = useRef<HTMLDivElement>(null);
  const navigationId = generateId('sidebar-nav');
  const userMenuId = generateId('user-menu');

  // 主功能菜单项 - 核心业务功能
  const mainMenuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/projects',
      icon: <ProjectOutlined />,
      label: '项目管理',
    },
    {
      key: '/annotation',
      icon: <FileTextOutlined />,
      label: 'CoT标注',
    },
    {
      key: '/knowledge-graph',
      icon: <BranchesOutlined />,
      label: '知识图谱',
    },
    {
      key: '/export',
      icon: <ExportOutlined />,
      label: '数据导出',
    },
  ];

  // 管理功能菜单项 - 系统管理功能
  const adminMenuItems = [
    {
      key: '/user-management',
      icon: <TeamOutlined />,
      label: '用户管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
    announceToScreenReader(`导航到 ${getMenuItemLabel(key)}`);
    
    // Close mobile sidebar after navigation
    if (isMobile && onMobileClose) {
      onMobileClose();
    }
  };

  // Get menu item label for announcements
  const getMenuItemLabel = (key: string): string => {
    const allItems = [...mainMenuItems, ...adminMenuItems];
    const item = allItems.find(item => item.key === key);
    return item?.label || key;
  };

  // 用户菜单处理
  const handleUserMenuClick: MenuProps['onClick'] = async ({ key }) => {
    if (key === 'logout') {
      try {
        announceToScreenReader('正在退出登录...', 'assertive');
        await authService.logout();
        navigate('/login');
        announceToScreenReader('已成功退出登录', 'assertive');
      } catch (error) {
        console.error('Logout error:', error);
        announceToScreenReader('退出登录失败', 'assertive');
      }
    } else if (key === 'profile') {
      navigate('/profile');
      announceToScreenReader('导航到个人资料页面');
    }
  };

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      label: '个人资料',
      icon: <UserOutlined />,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
    },
  ];

  // 响应式样式计算
  const logoSize = collapsed ? 24 : 32;
  const headerPadding = collapsed ? '0' : (isMobile ? '0 16px' : '0 24px');

  // Keyboard navigation for sidebar
  useKeyboardNavigation(
    // Escape key - close mobile sidebar
    isMobile ? onMobileClose : undefined,
    // Enter key - not used at sidebar level
    undefined,
    // Arrow keys - focus management
    (direction) => {
      if (direction === 'down' || direction === 'up') {
        // Let Menu component handle arrow navigation
        return;
      }
    }
  );

  // Skip link setup
  useEffect(() => {
    if (!sidebarRef.current) return;

    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.textContent = '跳转到主内容';
    skipLink.className = 'skip-link';
    skipLink.setAttribute('aria-label', '跳过导航，直接到主内容区域');
    
    // Insert skip link at the beginning of sidebar
    sidebarRef.current.insertBefore(skipLink, sidebarRef.current.firstChild);

    return () => {
      if (skipLink.parentNode) {
        skipLink.parentNode.removeChild(skipLink);
      }
    };
  }, []);

  return (
    <nav
      ref={sidebarRef}
      role="navigation"
      aria-label="主导航"
      aria-expanded={!collapsed}
      className="sidebar-navigation"
      style={{
        height: '100vh',
        background: '#001529', // 深蓝色背景，符合设计系统
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '2px 0 8px 0 rgba(29, 35, 41, 0.05)',
        borderRight: '1px solid rgba(255, 255, 255, 0.06)'
      }}
    >
      {/* Logo区域 - 品牌标识 */}
      <header
        role="banner"
        aria-label="COT Studio 标志"
        style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: headerPadding,
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(255, 255, 255, 0.02)',
          flexShrink: 0,
          transition: 'all 0.2s ease'
        }}
      >
        {collapsed ? (
          <div 
            role="img"
            aria-label="COT Studio 标志"
            style={{
              width: `${logoSize}px`,
              height: `${logoSize}px`,
              background: 'linear-gradient(135deg, #1677ff 0%, #69c0ff 100%)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <ScreenReaderOnly>COT Studio</ScreenReaderOnly>
            COT
          </div>
        ) : (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: isMobile ? '8px' : '12px',
            overflow: 'hidden'
          }}>
            <div 
              role="img"
              aria-label="COT Studio 标志"
              style={{
                width: `${logoSize}px`,
                height: `${logoSize}px`,
                background: 'linear-gradient(135deg, #1890ff 0%, #69c0ff 100%)',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 'bold',
                fontSize: '12px',
                flexShrink: 0
              }}
            >
              COT
            </div>
            <span style={{ 
              fontWeight: 600, 
              color: '#ffffff', 
              fontSize: isMobile ? '14px' : '16px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}>
              COT Studio
            </span>
          </div>
        )}
      </header>

      {/* 主菜单区域 */}
      <div 
        role="region"
        aria-labelledby={navigationId}
        style={{ 
          flex: 1, 
          overflow: 'auto',
          paddingTop: '16px'
        }}
      >
        <ScreenReaderOnly>
          <h2 id={navigationId}>主要功能导航</h2>
        </ScreenReaderOnly>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={mainMenuItems.map(item => ({
            ...item,
            'aria-label': `导航到${item.label}`,
            className: 'sidebar-nav-item'
          }))}
          onClick={handleMenuClick}
          theme="dark"
          role="menubar"
          aria-label="主要功能菜单"
          style={{ 
            borderRight: 0,
            background: 'transparent',
            fontSize: isMobile ? '13px' : '14px',
          }}
          inlineCollapsed={collapsed}
        />
        
        {/* 分割线 */}
        <div 
          role="separator"
          aria-hidden="true"
          style={{
            margin: '16px 12px',
            height: '1px',
            background: 'rgba(255, 255, 255, 0.1)'
          }} 
        />
        
        {/* 管理菜单 */}
        <div role="region" aria-label="管理功能">
          <ScreenReaderOnly>
            <h3>管理功能</h3>
          </ScreenReaderOnly>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={adminMenuItems.map(item => ({
              ...item,
              'aria-label': `导航到${item.label}`,
              className: 'sidebar-nav-item'
            }))}
            onClick={handleMenuClick}
            theme="dark"
            role="menubar"
            aria-label="管理功能菜单"
            style={{ 
              borderRight: 0,
              background: 'transparent',
              fontSize: isMobile ? '13px' : '14px',
            }}
            inlineCollapsed={collapsed}
          />
        </div>
      </div>

      {/* 底部功能区域 */}
      <footer
        role="contentinfo"
        aria-label="用户控制区域"
        style={{
          padding: collapsed ? '12px 8px' : '16px 12px',
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          background: 'rgba(255, 255, 255, 0.05)'
        }}
      >
        {/* 通知按钮 */}
        {!collapsed && (
          <div style={{ marginBottom: '12px' }}>
            <Button
              type="text"
              icon={<BellOutlined />}
              aria-label="通知中心，当前无新通知"
              aria-describedby="notification-status"
              style={{
                width: '100%',
                height: '36px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-start',
                color: 'rgba(255, 255, 255, 0.85)',
                border: 'none',
                borderRadius: '8px',
                background: 'transparent',
                fontSize: '14px',
                fontWeight: 500,
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
              className="notification-btn enhanced-sidebar-btn"
            >
              <Space>
                <Badge count={0} size="small">
                  <BellOutlined style={{ color: 'rgba(255, 255, 255, 0.85)' }} />
                </Badge>
                <span>通知中心</span>
              </Space>
            </Button>
            <ScreenReaderOnly>
              <div id="notification-status">当前没有新通知</div>
            </ScreenReaderOnly>
          </div>
        )}

        {/* 用户信息区域 */}
        {collapsed ? (
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            {/* 通知图标 - 折叠状态 */}
            <Button
              type="text"
              aria-label="通知中心，当前无新通知"
              title="通知中心"
              style={{
                width: '100%',
                height: '32px',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
              className="enhanced-sidebar-btn"
            >
              <Badge count={0} size="small">
                <BellOutlined style={{ fontSize: '16px', color: 'rgba(255, 255, 255, 0.85)' }} />
              </Badge>
            </Button>
            
            {/* 用户头像 - 折叠状态 */}
            <Dropdown 
              menu={{ 
                items: userMenuItems, 
                onClick: handleUserMenuClick,
                'aria-labelledby': userMenuId
              }}
              placement="topLeft"
              trigger={['click']}
            >
              <Button
                type="text"
                id={userMenuId}
                aria-label="用户菜单，当前用户：管理员"
                aria-haspopup="true"
                aria-expanded="false"
                title="用户菜单"
                style={{
                  width: '100%',
                  height: '40px',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
                }}
                className="enhanced-sidebar-btn"
              >
                <Avatar 
                  size={28} 
                  icon={<UserOutlined />}
                  alt="管理员头像"
                  style={{ 
                    background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)'
                  }}
                />
              </Button>
            </Dropdown>
          </Space>
        ) : (
          <Dropdown 
            menu={{ 
              items: userMenuItems, 
              onClick: handleUserMenuClick,
              'aria-labelledby': userMenuId
            }}
            placement="topLeft"
            trigger={['click']}
          >
            <Button
              type="text"
              id={userMenuId}
              aria-label="用户菜单，当前用户：管理员"
              aria-haspopup="true"
              aria-expanded="false"
              style={{
                width: '100%',
                height: '56px',
                padding: '8px 12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-start',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                background: 'transparent',
                fontWeight: 500,
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
              className="user-profile-btn enhanced-sidebar-btn"
            >
              <Space size="middle">
                <Avatar 
                  size={36} 
                  icon={<UserOutlined />}
                  alt="管理员头像"
                  style={{ 
                    background: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)'
                  }}
                />
                <div style={{ textAlign: 'left' }}>
                  <div style={{ 
                    fontSize: '14px', 
                    fontWeight: 600,
                    color: '#ffffff',
                    lineHeight: 1.2
                  }}>
                    管理员
                  </div>
                  <div style={{ 
                    fontSize: '12px', 
                    color: 'rgba(255, 255, 255, 0.65)',
                    lineHeight: 1.2,
                    marginTop: '2px'
                  }}>
                    Administrator
                  </div>
                </div>
              </Space>
            </Button>
          </Dropdown>
        )}
      </footer>
      
      {/* Enhanced Sidebar Styles */}
      <style>{`
        .enhanced-sidebar-btn:hover {
          background: rgba(255, 255, 255, 0.1) !important;
          transform: translateY(-1px);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }
        
        .enhanced-sidebar-btn:active {
          transform: translateY(0);
        }
        
        .enhanced-sidebar-btn:focus-visible {
          outline: 2px solid rgba(255, 255, 255, 0.5);
          outline-offset: 2px;
        }
        
        .notification-btn:hover {
          background: rgba(22, 119, 255, 0.15) !important;
        }
        
        .user-profile-btn:hover {
          background: rgba(255, 255, 255, 0.08) !important;
        }
        
        /* Menu item enhancements */
        .ant-menu-dark .ant-menu-item {
          border-radius: 8px !important;
          margin: 4px 8px !important;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
          font-weight: 500 !important;
        }
        
        .ant-menu-dark .ant-menu-item:hover {
          background: rgba(255, 255, 255, 0.1) !important;
          transform: translateX(2px);
        }
        
        .ant-menu-dark .ant-menu-item-selected {
          background: rgba(22, 119, 255, 0.2) !important;
          border-left: 3px solid #1677ff;
          font-weight: 600 !important;
        }
        
        .ant-menu-dark .ant-menu-item-icon {
          transition: all 0.2s ease !important;
        }
        
        .ant-menu-dark .ant-menu-item:hover .ant-menu-item-icon {
          transform: scale(1.1);
        }
        
        /* Logo animation */
        .logo-container {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .logo-container:hover {
          transform: scale(1.05);
        }
        
        /* Accessibility improvements */
        @media (prefers-reduced-motion: reduce) {
          .enhanced-sidebar-btn,
          .ant-menu-dark .ant-menu-item,
          .logo-container {
            transition: none !important;
            transform: none !important;
          }
        }
        
        /* High contrast mode */
        @media (prefers-contrast: high) {
          .enhanced-sidebar-btn:hover {
            background: rgba(255, 255, 255, 0.3) !important;
            border: 1px solid rgba(255, 255, 255, 0.5);
          }
          
          .ant-menu-dark .ant-menu-item-selected {
            border-left-width: 4px !important;
          }
        }
      `}</style>
    </nav>
  );
};

export default Sidebar;