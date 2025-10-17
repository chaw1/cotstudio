import React from 'react';
import { Card, Select, Button, Space, Slider, Typography, Divider, Tooltip } from 'antd';
import { 
  ReloadOutlined, 
  DownloadOutlined, 
  FullscreenOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  AimOutlined
} from '@ant-design/icons';
import { ViewportState } from './types';

const { Title, Text } = Typography;
const { Option } = Select;

interface KGControlPanelProps {
  currentLayout: string;
  onLayoutChange: (layout: string) => void;
  onReset: () => void;
  onExport: (format: 'png' | 'jpg') => void;
  viewport: ViewportState;
  nodeCount: number;
  edgeCount: number;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onFitToView?: () => void;
}

const KGControlPanel: React.FC<KGControlPanelProps> = ({
  currentLayout,
  onLayoutChange,
  onReset,
  onExport,
  viewport,
  nodeCount,
  edgeCount,
  onZoomIn,
  onZoomOut,
  onFitToView
}) => {
  const layoutOptions = [
    { value: 'cose', label: '力导向布局 (CoSE)', description: '适合复杂网络结构' },
    { value: 'circle', label: '圆形布局', description: '节点排列成圆形' },
    { value: 'grid', label: '网格布局', description: '节点排列成网格' },
    { value: 'random', label: '随机布局', description: '随机分布节点' },
    { value: 'concentric', label: '同心圆布局', description: '按重要性分层' },
    { value: 'breadthfirst', label: '广度优先布局', description: '按层级展开' }
  ];

  const densityOptions = [
    { value: 0.1, label: '稀疏' },
    { value: 0.3, label: '适中' },
    { value: 0.5, label: '密集' },
    { value: 0.8, label: '非常密集' }
  ];

  return (
    <Card title="图谱控制" size="small" style={{ marginBottom: 16 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 统计信息 */}
        <div>
          <Title level={5}>图谱统计</Title>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">节点数量:</Text>
              <Text strong>{nodeCount}</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">边数量:</Text>
              <Text strong>{edgeCount}</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">缩放比例:</Text>
              <Text strong>{(viewport.zoom * 100).toFixed(0)}%</Text>
            </div>
          </Space>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* 布局控制 */}
        <div>
          <Title level={5}>布局算法</Title>
          <Select
            value={currentLayout}
            onChange={onLayoutChange}
            style={{ width: '100%' }}
            placeholder="选择布局算法"
          >
            {layoutOptions.map(option => (
              <Option key={option.value} value={option.value}>
                <Tooltip title={option.description} placement="right">
                  {option.label}
                </Tooltip>
              </Option>
            ))}
          </Select>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* 视图控制 */}
        <div>
          <Title level={5}>视图控制</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Button
              icon={<AimOutlined />}
              onClick={onReset}
              block
              type="default"
            >
              重置视图
            </Button>
            
            <Button
              icon={<ReloadOutlined />}
              onClick={() => window.location.reload()}
              block
              type="default"
            >
              刷新数据
            </Button>
          </Space>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* 导出功能 */}
        <div>
          <Title level={5}>导出图谱</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Button
              icon={<DownloadOutlined />}
              onClick={() => onExport('png')}
              block
              type="primary"
            >
              导出 PNG
            </Button>
            
            <Button
              icon={<DownloadOutlined />}
              onClick={() => onExport('jpg')}
              block
              type="default"
            >
              导出 JPG
            </Button>
          </Space>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* 显示设置 */}
        <div>
          <Title level={5}>显示设置</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>节点大小</Text>
              <Slider
                min={10}
                max={100}
                defaultValue={30}
                marks={{
                  10: '小',
                  30: '中',
                  60: '大',
                  100: '特大'
                }}
                tooltip={{ formatter: (value) => `${value}px` }}
              />
            </div>
            
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>边粗细</Text>
              <Slider
                min={1}
                max={10}
                defaultValue={2}
                marks={{
                  1: '细',
                  3: '中',
                  6: '粗',
                  10: '特粗'
                }}
                tooltip={{ formatter: (value) => `${value}px` }}
              />
            </div>
            
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>标签大小</Text>
              <Slider
                min={8}
                max={20}
                defaultValue={12}
                marks={{
                  8: '小',
                  12: '中',
                  16: '大',
                  20: '特大'
                }}
                tooltip={{ formatter: (value) => `${value}px` }}
              />
            </div>
          </Space>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* 图谱密度控制 */}
        <div>
          <Title level={5}>图谱密度</Title>
          <Select
            defaultValue={0.3}
            style={{ width: '100%' }}
            placeholder="选择显示密度"
          >
            {densityOptions.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
          <Text type="secondary" style={{ fontSize: '11px', marginTop: '4px', display: 'block' }}>
            控制显示的节点和边的数量
          </Text>
        </div>

        {/* 快捷操作 */}
        <div style={{ marginTop: '16px' }}>
          <Space wrap>
            <Tooltip title="放大">
              <Button 
                icon={<ZoomInOutlined />} 
                size="small"
                onClick={onZoomIn}
                disabled={!onZoomIn}
              />
            </Tooltip>
            
            <Tooltip title="缩小">
              <Button 
                icon={<ZoomOutOutlined />} 
                size="small"
                onClick={onZoomOut}
                disabled={!onZoomOut}
              />
            </Tooltip>
            
            <Tooltip title="适合窗口">
              <Button 
                icon={<AimOutlined />} 
                size="small"
                onClick={onFitToView}
                disabled={!onFitToView}
              />
            </Tooltip>
            
            <Tooltip title="全屏">
              <Button 
                icon={<FullscreenOutlined />} 
                size="small"
                onClick={() => {
                  // 这里可以添加全屏逻辑
                }}
              />
            </Tooltip>
          </Space>
        </div>
      </Space>
    </Card>
  );
};

export default KGControlPanel;