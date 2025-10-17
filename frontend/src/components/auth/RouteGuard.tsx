import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Result, Button } from 'antd';
import { LockOutlined } from '@ant-design/icons';

interface RouteGuardProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
  requiredRole?: string;
  fallback?: React.ReactNode;
}

// 模拟权限检查函数 - 实际项目中应该从用户状态或API获取
const checkPermissions = (requiredPermissions: string[]): boolean => {
  // 检查用户角色，如果是管理员角色则拥有所有权限
  const userRole = localStorage.getItem('userRole') || 'USER';
  if (userRole === 'SUPER_ADMIN' || userRole === 'ADMIN') {
    return true;
  }
  
  // 对于普通用户，检查具体权限
  const userPermissions = JSON.parse(localStorage.getItem('userPermissions') || '[]');
  return requiredPermissions.every(permission => userPermissions.includes(permission));
};

const checkRole = (requiredRole: string): boolean => {
  // 这里应该实现真实的角色检查逻辑
  const userRole = localStorage.getItem('userRole') || 'USER';
  
  // 简单的角色层级检查 - 统一转换为大写以避免大小写问题
  const roleHierarchy = {
    'SUPER_ADMIN': 4,
    'ADMIN': 3,
    'EDITOR': 2,
    'USER': 1,
    'VIEWER': 0
  };
  
  const userRoleLevel = roleHierarchy[userRole.toUpperCase() as keyof typeof roleHierarchy] || 0;
  const requiredRoleLevel = roleHierarchy[requiredRole.toUpperCase() as keyof typeof roleHierarchy] || 0;
  
  return userRoleLevel >= requiredRoleLevel;
};

const RouteGuard: React.FC<RouteGuardProps> = ({
  children,
  requiredPermissions = [],
  requiredRole,
  fallback
}) => {
  const location = useLocation();

  // 检查权限
  if (requiredPermissions.length > 0 && !checkPermissions(requiredPermissions)) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <Result
        status="403"
        icon={<LockOutlined />}
        title="权限不足"
        subTitle="抱歉，您没有访问此页面的权限。请联系管理员获取相应权限。"
        extra={
          <Button type="primary" onClick={() => window.history.back()}>
            返回上一页
          </Button>
        }
      />
    );
  }

  // 检查角色
  if (requiredRole && !checkRole(requiredRole)) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <Result
        status="403"
        icon={<LockOutlined />}
        title="角色权限不足"
        subTitle={`此页面需要 ${requiredRole} 角色权限。请联系管理员提升您的权限级别。`}
        extra={
          <Button type="primary" onClick={() => window.history.back()}>
            返回上一页
          </Button>
        }
      />
    );
  }

  return <>{children}</>;
};

export default RouteGuard;

// 便捷的高阶组件
export const withRouteGuard = (
  Component: React.ComponentType<any>,
  requiredPermissions?: string[],
  requiredRole?: string,
  fallback?: React.ReactNode
) => {
  const GuardedComponent = (props: any) => (
    <RouteGuard
      requiredPermissions={requiredPermissions}
      requiredRole={requiredRole}
      fallback={fallback}
    >
      <Component {...props} />
    </RouteGuard>
  );

  GuardedComponent.displayName = `withRouteGuard(${Component.displayName || Component.name})`;
  
  return GuardedComponent;
};