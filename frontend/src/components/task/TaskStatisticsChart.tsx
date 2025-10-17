/**
 * 任务统计图表组件
 */
import React from 'react';
import { Card, Row, Col, Empty } from 'antd';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

import { TaskStatistics, TASK_STATUS_COLORS, TASK_PRIORITY_COLORS } from '../../types/task';

interface TaskStatisticsChartProps {
  statistics: TaskStatistics | null;
}

const TaskStatisticsChart: React.FC<TaskStatisticsChartProps> = ({ statistics }) => {
  if (!statistics) {
    return (
      <div className="flex justify-center items-center h-64">
        <Empty description="暂无统计数据" />
      </div>
    );
  }

  // 准备状态分布数据
  const statusData = Object.entries(statistics.by_status).map(([status, count]) => ({
    name: status,
    value: count,
    color: TASK_STATUS_COLORS[status as keyof typeof TASK_STATUS_COLORS] || '#8884d8'
  }));

  // 准备类型分布数据
  const typeData = Object.entries(statistics.by_type).map(([type, count]) => ({
    name: type,
    value: count
  }));

  // 准备优先级分布数据
  const priorityData = Object.entries(statistics.by_priority).map(([priority, count]) => ({
    name: priority,
    value: count,
    color: TASK_PRIORITY_COLORS[priority as keyof typeof TASK_PRIORITY_COLORS] || '#8884d8'
  }));

  // 自定义饼图标签
  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    if (percent < 0.05) return null; // 小于5%不显示标签
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div className="space-y-6">
      {/* 总体统计 */}
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{statistics.total_tasks}</div>
              <div className="text-gray-500">总任务数</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{statistics.active_tasks}</div>
              <div className="text-gray-500">活跃任务</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {(statistics.success_rate * 100).toFixed(2)}%
              </div>
              <div className="text-gray-500">成功率</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {statistics.average_duration ? `${statistics.average_duration.toFixed(2)}s` : '-'}
              </div>
              <div className="text-gray-500">平均执行时间</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={16}>
        {/* 任务状态分布 */}
        <Col span={8}>
          <Card title="任务状态分布" size="small">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomizedLabel}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* 任务类型分布 */}
        <Col span={8}>
          <Card title="任务类型分布" size="small">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={typeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={10}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* 任务优先级分布 */}
        <Col span={8}>
          <Card title="任务优先级分布" size="small">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={priorityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderCustomizedLabel}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {priorityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* 详细统计表格 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card title="状态统计详情" size="small">
            <div className="space-y-2">
              {Object.entries(statistics.by_status).map(([status, count]) => (
                <div key={status} className="flex justify-between items-center">
                  <span className="flex items-center">
                    <div 
                      className="w-3 h-3 rounded-full mr-2"
                      style={{ 
                        backgroundColor: TASK_STATUS_COLORS[status as keyof typeof TASK_STATUS_COLORS] || '#8884d8'
                      }}
                    />
                    {status}
                  </span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="类型统计详情" size="small">
            <div className="space-y-2">
              {Object.entries(statistics.by_type).map(([type, count]) => (
                <div key={type} className="flex justify-between items-center">
                  <span>{type}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default TaskStatisticsChart;