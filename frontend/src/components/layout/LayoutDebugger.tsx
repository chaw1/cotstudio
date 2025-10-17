import React, { useState } from 'react';
import { Card, Switch, Descriptions, Tag, Button, Space, Drawer } from 'antd';
import { BugOutlined, EyeOutlined } from '@ant-design/icons';
import { LayoutDebugInfo } from '../../types/layout';
import { DEBUG_CONFIG } from '../../config/layout';

interface LayoutDebuggerProps {
  debugInfo: LayoutDebugInfo;
}

const LayoutDebugger: React.FC<LayoutDebuggerProps> = ({ debugInfo }) => {
  const [visible, setVisible] = useState(false);
  const [showGrid, setShowGrid] = useState<boolean>(DEBUG_CONFIG.showGrid);
  const [showBreakpoints, setShowBreakpoints] = useState<boolean>(DEBUG_CONFIG.showBreakpoints);
  const [showDimensions, setShowDimensions] = useState<boolean>(DEBUG_CONFIG.showDimensions);

  if (!DEBUG_CONFIG.enabled) {
    return null;
  }

  const { screenSize, breakpoint, layoutDimensions, performance, accessibility } = debugInfo;

  const getBreakpointColor = (bp: string) => {
    const colors = {
      xs: 'red',
      sm: 'orange', 
      md: 'gold',
      lg: 'green',
      xl: 'blue',
      xxl: 'purple'
    };
    return colors[bp as keyof typeof colors] || 'default';
  };

  const formatBytes = (bytes: number) => {
    return `${bytes}px`;
  };

  return (
    <>
      {/* 调试按钮 */}
      <div
        style={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          zIndex: 9999,
          background: '#1677ff',
          borderRadius: '50%',
          width: 48,
          height: 48,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(22, 119, 255, 0.3)',
          color: 'white'
        }}
        onClick={() => setVisible(true)}
      >
        <BugOutlined style={{ fontSize: 18 }} />
      </div>

      {/* 断点指示器 */}
      {showBreakpoints && (
        <div
          style={{
            position: 'fixed',
            top: 20,
            right: 20,
            zIndex: 9998,
            background: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontFamily: 'monospace'
          }}
        >
          <Tag color={getBreakpointColor(breakpoint)}>
            {breakpoint.toUpperCase()}
          </Tag>
          {screenSize.width} × {screenSize.height}
        </div>
      )}

      {/* 网格覆盖层 */}
      {showGrid && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            pointerEvents: 'none',
            zIndex: 9997,
            background: `
              linear-gradient(rgba(255, 0, 0, ${DEBUG_CONFIG.overlayOpacity}) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255, 0, 0, ${DEBUG_CONFIG.overlayOpacity}) 1px, transparent 1px)
            `,
            backgroundSize: '20px 20px'
          }}
        />
      )}

      {/* 尺寸指示器 */}
      {showDimensions && (
        <>
          {/* 侧边栏尺寸 */}
          <div
            style={{
              position: 'fixed',
              left: 0,
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'rgba(0, 0, 0, 0.8)',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '0 4px 4px 0',
              fontSize: '10px',
              fontFamily: 'monospace',
              zIndex: 9998
            }}
          >
            {formatBytes(layoutDimensions.sidebar.width)}
          </div>
          
          {/* 头部尺寸 */}
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'rgba(0, 0, 0, 0.8)',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '0 0 4px 4px',
              fontSize: '10px',
              fontFamily: 'monospace',
              zIndex: 9998
            }}
          >
            {formatBytes(layoutDimensions.header.height)}
          </div>
        </>
      )}

      {/* 调试面板 */}
      <Drawer
        title={
          <Space>
            <BugOutlined />
            布局调试器
          </Space>
        }
        placement="right"
        width={400}
        open={visible}
        onClose={() => setVisible(false)}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 调试选项 */}
          <Card title="调试选项" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>显示网格</span>
                <Switch 
                  checked={showGrid} 
                  onChange={(checked) => setShowGrid(checked)}
                  size="small"
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>显示断点</span>
                <Switch 
                  checked={showBreakpoints} 
                  onChange={(checked) => setShowBreakpoints(checked)}
                  size="small"
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>显示尺寸</span>
                <Switch 
                  checked={showDimensions} 
                  onChange={(checked) => setShowDimensions(checked)}
                  size="small"
                />
              </div>
            </Space>
          </Card>

          {/* 屏幕信息 */}
          <Card title="屏幕信息" size="small">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="分辨率">
                {screenSize.width} × {screenSize.height}
              </Descriptions.Item>
              <Descriptions.Item label="当前断点">
                <Tag color={getBreakpointColor(breakpoint)}>
                  {breakpoint.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="设备类型">
                {screenSize.width <= 767 ? '移动设备' : 
                 screenSize.width <= 1199 ? '平板设备' : '桌面设备'}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* 布局尺寸 */}
          <Card title="布局尺寸" size="small">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="头部高度">
                {formatBytes(layoutDimensions.header.height)}
              </Descriptions.Item>
              <Descriptions.Item label="侧边栏宽度">
                {formatBytes(layoutDimensions.sidebar.width)}
              </Descriptions.Item>
              <Descriptions.Item label="折叠宽度">
                {formatBytes(layoutDimensions.sidebar.collapsedWidth)}
              </Descriptions.Item>
              <Descriptions.Item label="内容边距">
                {formatBytes(layoutDimensions.content.margin)}
              </Descriptions.Item>
              <Descriptions.Item label="内容内边距">
                {formatBytes(layoutDimensions.content.padding)}
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* 性能信息 */}
          {performance && (
            <Card title="性能信息" size="small">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="渲染时间">
                  {performance.renderTime.toFixed(2)}ms
                </Descriptions.Item>
                <Descriptions.Item label="实际尺寸">
                  {performance.actualDimensions.width} × {performance.actualDimensions.height}
                </Descriptions.Item>
                <Descriptions.Item label="内容区域">
                  {performance.contentArea.width} × {performance.contentArea.height}
                </Descriptions.Item>
                {performance.memoryUsage && (
                  <Descriptions.Item label="内存使用">
                    {performance.memoryUsage.used}MB / {performance.memoryUsage.total}MB
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>
          )}

          {/* 无障碍信息 */}
          {accessibility && (
            <Card title="无障碍信息" size="small">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="减少动画">
                  <Tag color={accessibility.reducedMotion ? 'green' : 'default'}>
                    {accessibility.reducedMotion ? '是' : '否'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="高对比度">
                  <Tag color={accessibility.highContrast ? 'green' : 'default'}>
                    {accessibility.highContrast ? '是' : '否'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="颜色方案">
                  <Tag color={accessibility.colorScheme === 'dark' ? 'purple' : 'orange'}>
                    {accessibility.colorScheme === 'dark' ? '深色' : '浅色'}
                  </Tag>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          )}

          {/* 操作按钮 */}
          <Space style={{ width: '100%', justifyContent: 'center' }}>
            <Button 
              icon={<EyeOutlined />}
              onClick={() => console.log('Layout Debug Info:', debugInfo)}
            >
              输出到控制台
            </Button>
          </Space>
        </Space>
      </Drawer>
    </>
  );
};

export default LayoutDebugger;