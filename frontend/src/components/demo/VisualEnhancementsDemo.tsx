import React from 'react';
import { Space, Row, Col, Divider } from 'antd';
import EnhancedButton from '../common/EnhancedButton';
import InteractiveCard from '../common/InteractiveCard';
import StatusIndicator from '../common/StatusIndicator';
import { Title, Text, Paragraph } from '../common/Typography';

/**
 * VisualEnhancementsDemo - 视觉增强组件演示
 * 
 * 用于展示和测试新的视觉设计系统组件
 */
const VisualEnhancementsDemo: React.FC = () => {
  return (
    <div className="p-5">
      <Title variant="display" gradient>
        视觉设计系统演示
      </Title>
      
      <Paragraph variant="lead" spacing="relaxed">
        这里展示了新的视觉设计系统中的各种组件和交互效果。
      </Paragraph>

      <Divider />

      {/* 按钮系统演示 */}
      <section className="mb-6">
        <Title variant="heading">增强按钮系统</Title>
        <Text variant="body" color="secondary">
          支持多种变体、交互效果和无障碍优化
        </Text>
        
        <div className="mt-4">
          <Space wrap size="middle">
            <EnhancedButton variant="primary" interactive>
              主要按钮
            </EnhancedButton>
            <EnhancedButton variant="secondary" interactive>
              次要按钮
            </EnhancedButton>
            <EnhancedButton variant="success" interactive>
              成功按钮
            </EnhancedButton>
            <EnhancedButton variant="warning" interactive>
              警告按钮
            </EnhancedButton>
            <EnhancedButton variant="danger" interactive>
              危险按钮
            </EnhancedButton>
            <EnhancedButton variant="ghost" interactive>
              幽灵按钮
            </EnhancedButton>
            <EnhancedButton variant="text" interactive>
              文本按钮
            </EnhancedButton>
          </Space>
        </div>

        <div className="mt-4">
          <Text variant="caption" color="tertiary">
            不同尺寸和阴影效果：
          </Text>
          <div className="mt-2">
            <Space wrap>
              <EnhancedButton variant="primary" size="small" elevation="sm">
                小按钮
              </EnhancedButton>
              <EnhancedButton variant="primary" size="middle" elevation="md">
                中按钮
              </EnhancedButton>
              <EnhancedButton variant="primary" size="large" elevation="lg">
                大按钮
              </EnhancedButton>
              <EnhancedButton variant="primary" rounded>
                圆角按钮
              </EnhancedButton>
            </Space>
          </div>
        </div>
      </section>

      <Divider />

      {/* 交互式卡片演示 */}
      <section className="mb-6">
        <Title variant="heading">交互式卡片</Title>
        <Text variant="body" color="secondary">
          支持多种悬停效果、选中状态和视觉变体
        </Text>
        
        <Row gutter={[16, 16]} className="mt-4">
          <Col xs={24} sm={12} md={8}>
            <InteractiveCard
              title="悬停提升效果"
              hoverEffect="lift"
              clickable
              className="h-32"
            >
              <Text>鼠标悬停时会有提升动画效果</Text>
            </InteractiveCard>
          </Col>
          
          <Col xs={24} sm={12} md={8}>
            <InteractiveCard
              title="缩放效果"
              hoverEffect="scale"
              clickable
              variant="outlined"
              className="h-32"
            >
              <Text>鼠标悬停时会有缩放动画效果</Text>
            </InteractiveCard>
          </Col>
          
          <Col xs={24} sm={12} md={8}>
            <InteractiveCard
              title="发光效果"
              hoverEffect="glow"
              clickable
              variant="filled"
              className="h-32"
            >
              <Text>鼠标悬停时会有发光效果</Text>
            </InteractiveCard>
          </Col>
          
          <Col xs={24} sm={12} md={8}>
            <InteractiveCard
              title="玻璃态效果"
              hoverEffect="lift"
              clickable
              variant="glass"
              className="h-32"
            >
              <Text>现代化的玻璃态背景效果</Text>
            </InteractiveCard>
          </Col>
          
          <Col xs={24} sm={12} md={8}>
            <InteractiveCard
              title="选中状态"
              hoverEffect="lift"
              clickable
              selected
              className="h-32"
            >
              <Text>这是选中状态的卡片</Text>
            </InteractiveCard>
          </Col>
        </Row>
      </section>

      <Divider />

      {/* 状态指示器演示 */}
      <section className="mb-6">
        <Title variant="heading">状态指示器系统</Title>
        <Text variant="body" color="secondary">
          丰富的状态类型和视觉变体，支持动画效果
        </Text>
        
        <div className="mt-4">
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12}>
              <Text variant="label" color="primary">标签变体：</Text>
              <div className="mt-2">
                <Space wrap>
                  <StatusIndicator status="success" text="成功" />
                  <StatusIndicator status="warning" text="警告" />
                  <StatusIndicator status="error" text="错误" />
                  <StatusIndicator status="info" text="信息" />
                  <StatusIndicator status="processing" text="处理中" animated />
                  <StatusIndicator status="pending" text="等待中" />
                  <StatusIndicator status="offline" text="离线" />
                </Space>
              </div>
            </Col>
            
            <Col xs={24} sm={12}>
              <Text variant="label" color="primary">圆点变体：</Text>
              <div className="mt-2">
                <Space wrap>
                  <StatusIndicator status="success" variant="dot" />
                  <StatusIndicator status="warning" variant="dot" />
                  <StatusIndicator status="error" variant="dot" />
                  <StatusIndicator status="processing" variant="dot" animated />
                </Space>
              </div>
            </Col>
            
            <Col xs={24} sm={12}>
              <Text variant="label" color="primary">图标变体：</Text>
              <div className="mt-2">
                <Space wrap direction="vertical">
                  <StatusIndicator status="success" variant="icon" text="操作成功" />
                  <StatusIndicator status="warning" variant="icon" text="需要注意" />
                  <StatusIndicator status="error" variant="icon" text="操作失败" />
                  <StatusIndicator status="processing" variant="icon" text="正在处理" animated />
                </Space>
              </div>
            </Col>
            
            <Col xs={24} sm={12}>
              <Text variant="label" color="primary">徽章变体：</Text>
              <div className="mt-2">
                <Space wrap direction="vertical">
                  <StatusIndicator status="success" variant="badge" text="已完成" />
                  <StatusIndicator status="warning" variant="badge" text="待处理" />
                  <StatusIndicator status="error" variant="badge" text="已失败" />
                  <StatusIndicator status="info" variant="badge" text="新消息" />
                </Space>
              </div>
            </Col>
          </Row>
        </div>
      </section>

      <Divider />

      {/* 排版系统演示 */}
      <section className="mb-6">
        <Title variant="heading">增强排版系统</Title>
        <Text variant="body" color="secondary">
          现代化的字体层级和间距系统
        </Text>
        
        <div className="mt-4">
          <Title variant="display" weight="bold">
            Display 标题 - 用于重要展示
          </Title>
          <Title variant="heading" weight="semibold">
            Heading 标题 - 用于章节标题
          </Title>
          <Title variant="subheading" weight="medium">
            Subheading 副标题 - 用于小节标题
          </Title>
          
          <Paragraph variant="lead" spacing="relaxed">
            这是引导段落，通常用于文章开头或重要说明。字体稍大，行距较宽松，便于阅读。
          </Paragraph>
          
          <Paragraph variant="body" spacing="normal">
            这是正文段落，是最常用的文本样式。具有适中的字体大小和行距，适合长篇阅读。
            支持多种文本颜色和权重设置。
          </Paragraph>
          
          <div className="mt-4">
            <Space wrap>
              <Text variant="body" color="primary">主要文本</Text>
              <Text variant="body" color="secondary">次要文本</Text>
              <Text variant="body" color="tertiary">第三级文本</Text>
              <Text variant="caption" color="secondary">说明文字</Text>
              <Text variant="overline" color="tertiary">OVERLINE TEXT</Text>
              <Text variant="label" weight="medium">标签文本</Text>
            </Space>
          </div>
        </div>
      </section>

      <Divider />

      {/* 间距系统演示 */}
      <section className="mb-6">
        <Title variant="heading">间距系统</Title>
        <Text variant="body" color="secondary">
          基于8px网格的一致性间距系统
        </Text>
        
        <div className="mt-4">
          <Text variant="label" color="primary">边距示例：</Text>
          <div className="mt-2 p-3 bg-gray-50 rounded">
            <div className="m-1 p-2 bg-blue-100 rounded">m-1 (8px)</div>
            <div className="m-2 p-2 bg-blue-100 rounded">m-2 (12px)</div>
            <div className="m-3 p-2 bg-blue-100 rounded">m-3 (16px)</div>
          </div>
          
          <Text variant="label" color="primary" className="mt-4 block">内边距示例：</Text>
          <div className="mt-2">
            <Space wrap>
              <div className="p-1 bg-green-100 rounded">p-1 (8px)</div>
              <div className="p-2 bg-green-100 rounded">p-2 (12px)</div>
              <div className="p-3 bg-green-100 rounded">p-3 (16px)</div>
              <div className="p-4 bg-green-100 rounded">p-4 (20px)</div>
              <div className="p-5 bg-green-100 rounded">p-5 (24px)</div>
            </Space>
          </div>
        </div>
      </section>
    </div>
  );
};

export default VisualEnhancementsDemo;