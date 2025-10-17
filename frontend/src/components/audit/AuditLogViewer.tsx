import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Space,
  Button,
  Input,
  Select,
  DatePicker,
  Tag,
  Tooltip,
  Descriptions,
  Alert,
  Row,
  Col,
  Statistic,
  Typography
} from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  EyeOutlined,
  ReloadOutlined,
  DownloadOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import ModalContainer from '../common/ModalContainer';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Text } = Typography;

interface AuditLog {
  id: string;
  user_id?: string;
  event_type: string;
  severity: string;
  resource_type?: string;
  resource_id?: string;
  resource_name?: string;
  action: string;
  description?: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  success: boolean;
  error_message?: string;
  created_at: string;
}

interface AuditStatistics {
  total_operations: number;
  failed_operations: number;
  success_rate: number;
  active_users: number;
  event_type_distribution: Record<string, number>;
  severity_distribution: Record<string, number>;
  resource_type_distribution: Record<string, number>;
}

interface AuditLogViewerProps {
  projectId?: string;
}

const AuditLogViewer: React.FC<AuditLogViewerProps> = ({ projectId }) => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [statistics, setStatistics] = useState<AuditStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  
  // 过滤条件
  const [filters, setFilters] = useState({
    search_text: '',
    event_types: [],
    severity: undefined,
    resource_type: undefined,
    success: undefined,
    date_range: null as [dayjs.Dayjs, dayjs.Dayjs] | null,
    user_id: ''
  });

  const eventTypeOptions = [
    { value: 'create', label: '创建', color: 'green' },
    { value: 'read', label: '查看', color: 'blue' },
    { value: 'update', label: '更新', color: 'orange' },
    { value: 'delete', label: '删除', color: 'red' },
    { value: 'login', label: '登录', color: 'cyan' },
    { value: 'logout', label: '登出', color: 'gray' },
    { value: 'permission_change', label: '权限变更', color: 'purple' },
    { value: 'export', label: '导出', color: 'magenta' },
    { value: 'import', label: '导入', color: 'lime' },
    { value: 'system_config', label: '系统配置', color: 'volcano' }
  ];

  const severityOptions = [
    { value: 'low', label: '低', color: 'default' },
    { value: 'medium', label: '中', color: 'warning' },
    { value: 'high', label: '高', color: 'error' },
    { value: 'critical', label: '严重', color: 'error' }
  ];

  const resourceTypeOptions = [
    { value: 'project', label: '项目' },
    { value: 'file', label: '文件' },
    { value: 'cot_item', label: 'CoT数据' },
    { value: 'user', label: '用户' },
    { value: 'role', label: '角色' },
    { value: 'permission', label: '权限' },
    { value: 'system_setting', label: '系统设置' },
    { value: 'knowledge_graph', label: '知识图谱' }
  ];

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        size: pageSize.toString()
      });

      // 添加过滤条件
      if (filters.search_text) {
        params.append('search_text', filters.search_text);
      }
      if (filters.event_types.length > 0) {
        filters.event_types.forEach(type => params.append('event_types', type));
      }
      if (filters.severity) {
        params.append('severity', filters.severity);
      }
      if (filters.resource_type) {
        params.append('resource_type', filters.resource_type);
      }
      if (filters.success !== undefined) {
        params.append('success', filters.success.toString());
      }
      if (filters.date_range) {
        params.append('start_date', filters.date_range[0].toISOString());
        params.append('end_date', filters.date_range[1].toISOString());
      }
      if (filters.user_id) {
        params.append('user_id', filters.user_id);
      }

      const response = await fetch(`/api/v1/audit/logs?${params}`);
      const data = await response.json();

      if (response.ok) {
        setLogs(data.items);
        setTotal(data.total);
      } else {
        throw new Error(data.detail || '获取审计日志失败');
      }
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.date_range) {
        params.append('start_date', filters.date_range[0].toISOString());
        params.append('end_date', filters.date_range[1].toISOString());
      }

      const response = await fetch(`/api/v1/audit/statistics?${params}`);
      const data = await response.json();

      if (response.ok) {
        setStatistics(data);
      }
    } catch (error) {
      console.error('Failed to fetch audit statistics:', error);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
    fetchStatistics();
  }, [currentPage, pageSize]);

  const handleSearch = () => {
    setCurrentPage(1);
    fetchAuditLogs();
    fetchStatistics();
  };

  const handleReset = () => {
    setFilters({
      search_text: '',
      event_types: [],
      severity: undefined,
      resource_type: undefined,
      success: undefined,
      date_range: null,
      user_id: ''
    });
    setCurrentPage(1);
  };

  const showLogDetail = (log: AuditLog) => {
    setSelectedLog(log);
    setDetailModalVisible(true);
  };

  const getEventTypeTag = (eventType: string) => {
    const option = eventTypeOptions.find(opt => opt.value === eventType);
    return (
      <Tag color={option?.color || 'default'}>
        {option?.label || eventType}
      </Tag>
    );
  };

  const getSeverityTag = (severity: string) => {
    const option = severityOptions.find(opt => opt.value === severity);
    return (
      <Tag color={option?.color || 'default'}>
        {option?.label || severity}
      </Tag>
    );
  };

  const columns: ColumnsType<AuditLog> = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
      sorter: true
    },
    {
      title: '用户',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 120,
      render: (text: string) => text || '系统'
    },
    {
      title: '事件类型',
      dataIndex: 'event_type',
      key: 'event_type',
      width: 100,
      render: getEventTypeTag
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 80,
      render: getSeverityTag
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 120
    },
    {
      title: '资源',
      key: 'resource',
      width: 150,
      render: (_, record) => {
        if (record.resource_type) {
          const resourceOption = resourceTypeOptions.find(opt => opt.value === record.resource_type);
          return (
            <div>
              <div>{resourceOption?.label || record.resource_type}</div>
              {record.resource_name && (
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {record.resource_name}
                </Text>
              )}
            </div>
          );
        }
        return '-';
      }
    },
    {
      title: '状态',
      dataIndex: 'success',
      key: 'success',
      width: 80,
      render: (success: boolean) => (
        success ? (
          <CheckCircleOutlined style={{ color: '#52c41a' }} />
        ) : (
          <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
        )
      )
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 120,
      render: (text: string) => text || '-'
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => showLogDetail(record)}
        >
          详情
        </Button>
      )
    }
  ];

  return (
    <div>
      {/* 统计信息 */}
      {statistics && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总操作数"
                value={statistics.total_operations}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="失败操作"
                value={statistics.failed_operations}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="成功率"
                value={statistics.success_rate}
                precision={1}
                suffix="%"
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="活跃用户"
                value={statistics.active_users}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 过滤器 */}
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input
            placeholder="搜索操作、描述或资源名称"
            value={filters.search_text}
            onChange={(e) => setFilters({ ...filters, search_text: e.target.value })}
            style={{ width: 200 }}
            prefix={<SearchOutlined />}
          />
          
          <Select
            mode="multiple"
            placeholder="事件类型"
            value={filters.event_types}
            onChange={(value) => setFilters({ ...filters, event_types: value })}
            style={{ width: 150 }}
          >
            {eventTypeOptions.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>

          <Select
            placeholder="严重程度"
            value={filters.severity}
            onChange={(value) => setFilters({ ...filters, severity: value })}
            style={{ width: 120 }}
            allowClear
          >
            {severityOptions.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>

          <Select
            placeholder="资源类型"
            value={filters.resource_type}
            onChange={(value) => setFilters({ ...filters, resource_type: value })}
            style={{ width: 120 }}
            allowClear
          >
            {resourceTypeOptions.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>

          <Select
            placeholder="操作状态"
            value={filters.success}
            onChange={(value) => setFilters({ ...filters, success: value })}
            style={{ width: 100 }}
            allowClear
          >
            <Option value={true}>成功</Option>
            <Option value={false}>失败</Option>
          </Select>

          <RangePicker
            value={filters.date_range}
            onChange={(dates) => setFilters({ ...filters, date_range: dates })}
            showTime
            format="YYYY-MM-DD HH:mm"
          />

          <Input
            placeholder="用户ID"
            value={filters.user_id}
            onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
            style={{ width: 120 }}
          />

          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
            搜索
          </Button>
          
          <Button icon={<FilterOutlined />} onClick={handleReset}>
            重置
          </Button>
          
          <Button icon={<ReloadOutlined />} onClick={() => {
            fetchAuditLogs();
            fetchStatistics();
          }}>
            刷新
          </Button>
        </Space>
      </Card>

      {/* 审计日志表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, size) => {
              setCurrentPage(page);
              setPageSize(size || 50);
            }
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 详情模态框 */}
      <ModalContainer
        visible={detailModalVisible}
        onClose={() => setDetailModalVisible(false)}
        title="审计日志详情"
        width={800}
        footer={null}
      >
        {selectedLog && (
          <div>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="时间">
                {dayjs(selectedLog.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="用户ID">
                {selectedLog.user_id || '系统'}
              </Descriptions.Item>
              <Descriptions.Item label="事件类型">
                {getEventTypeTag(selectedLog.event_type)}
              </Descriptions.Item>
              <Descriptions.Item label="严重程度">
                {getSeverityTag(selectedLog.severity)}
              </Descriptions.Item>
              <Descriptions.Item label="操作">
                {selectedLog.action}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                {selectedLog.success ? (
                  <Tag color="success">成功</Tag>
                ) : (
                  <Tag color="error">失败</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="资源类型">
                {selectedLog.resource_type || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="资源ID">
                {selectedLog.resource_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="资源名称" span={2}>
                {selectedLog.resource_name || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="IP地址">
                {selectedLog.ip_address || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="用户代理" span={2}>
                {selectedLog.user_agent || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>
                {selectedLog.description || '-'}
              </Descriptions.Item>
            </Descriptions>

            {selectedLog.error_message && (
              <Alert
                message="错误信息"
                description={selectedLog.error_message}
                type="error"
                style={{ marginTop: 16 }}
              />
            )}

            {Object.keys(selectedLog.details).length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text strong>详细信息：</Text>
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: 12, 
                  borderRadius: 4,
                  marginTop: 8,
                  overflow: 'auto'
                }}>
                  {JSON.stringify(selectedLog.details, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </ModalContainer>
    </div>
  );
};

export default AuditLogViewer;