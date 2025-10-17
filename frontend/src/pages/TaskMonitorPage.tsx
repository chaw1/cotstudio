/**
 * 任务监控页面
 */
import React from 'react';
import TaskMonitorDashboard from '../components/task/TaskMonitorDashboard';

const TaskMonitorPage: React.FC = () => {
  // 这里应该从认证上下文或状态管理中获取用户ID
  // 暂时使用硬编码的用户ID作为示例
  const userId = 'current_user_id'; // 实际应用中应该从认证状态获取

  return (
    <div className="min-h-screen bg-gray-50">
      <TaskMonitorDashboard userId={userId} />
    </div>
  );
};

export default TaskMonitorPage;