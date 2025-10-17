import { createBrowserRouter, Navigate } from 'react-router-dom';
import { MainLayout } from '../components/layout';
import ErrorBoundary from '../components/ErrorBoundary';
import { Login, ProtectedRoute, RouteGuard } from '../components/auth';
import { createLazyPageComponent, preloadComponent } from '../utils/lazyLoading';

// 懒加载页面组件
const Dashboard = createLazyPageComponent(() => import('../pages/Dashboard'));
const Projects = createLazyPageComponent(() => import('../pages/Projects'));
const Annotation = createLazyPageComponent(() => import('../pages/Annotation'));
const AnnotationProjects = createLazyPageComponent(() => import('../pages/AnnotationProjects'));
const KnowledgeGraph = createLazyPageComponent(() => import('../pages/KnowledgeGraph'));
const KnowledgeGraphList = createLazyPageComponent(() => import('../pages/KnowledgeGraphList'));
const Export = createLazyPageComponent(() => import('../pages/Export'));
const Settings = createLazyPageComponent(() => import('../pages/Settings'));
const UserManagement = createLazyPageComponent(() => import('../pages/UserManagement'));
const DebugLogin = createLazyPageComponent(() => import('../pages/DebugLogin'));
const TestPage = createLazyPageComponent(() => import('../pages/TestPage'));

// 预加载关键页面
preloadComponent(() => import('../pages/Dashboard'));
preloadComponent(() => import('../pages/Projects'));

const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <ErrorBoundary>
        <Login />
      </ErrorBoundary>
    ),
  },
  {
    path: '/debug-login',
    element: (
      <ErrorBoundary>
        <DebugLogin />
      </ErrorBoundary>
    ),
  },
  {
    path: '/',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <Navigate to="/dashboard" replace />
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '/dashboard',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <Dashboard />
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '/projects',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <Projects />
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '/annotation',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <AnnotationProjects />
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '/annotation/:projectId',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <Annotation />
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '/knowledge-graph',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <KnowledgeGraphList />
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '/knowledge-graph/:projectId',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <KnowledgeGraph />
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '/projects/:projectId/knowledge-graph',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <KnowledgeGraph />
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '/export',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <Export />
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '/settings',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <RouteGuard requiredRole="ADMIN">
              <Settings />
            </RouteGuard>
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '/user-management',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <RouteGuard requiredRole="ADMIN">
              <UserManagement />
            </RouteGuard>
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '*',
    element: (
      <ErrorBoundary>
        <ProtectedRoute>
          <MainLayout>
            <Navigate to="/dashboard" replace />
          </MainLayout>
        </ProtectedRoute>
      </ErrorBoundary>
    ),
  },
  {
    path: '/test',
    element: (
      <ErrorBoundary>
        <TestPage />
      </ErrorBoundary>
    ),
  },
], {
  // future: {
  //   v7_startTransition: true,
  // },
});

export default router;