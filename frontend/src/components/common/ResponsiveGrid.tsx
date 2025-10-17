import React from 'react';
import { Row, Col } from 'antd';
import { useResponsiveBreakpoint } from '../../hooks/useResponsiveBreakpoint';

interface ResponsiveGridProps {
  children: React.ReactNode;
  gutter?: number | [number, number];
  columns?: {
    xs?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
    xxl?: number;
  };
  className?: string;
  style?: React.CSSProperties;
}

/**
 * 响应式网格组件，自动适配不同屏幕尺寸的列数
 */
const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  gutter,
  columns = { xs: 1, sm: 2, md: 2, lg: 3, xl: 4, xxl: 4 },
  className = '',
  style = {}
}) => {
  const { isMobile, isTablet, breakpoint } = useResponsiveBreakpoint();

  // 计算响应式间距
  const responsiveGutter = gutter || (isMobile ? [8, 8] : isTablet ? [16, 16] : [24, 24]);

  // 计算每个子元素的列宽
  const getColSpan = () => {
    const currentColumns = columns[breakpoint] || columns.lg || 3;
    return 24 / currentColumns;
  };

  const colSpan = getColSpan();

  return (
    <Row 
      gutter={responsiveGutter}
      className={`responsive-grid ${className}`}
      style={style}
    >
      {React.Children.map(children, (child, index) => (
        <Col 
          key={index}
          xs={24 / (columns.xs || 1)}
          sm={24 / (columns.sm || 2)}
          md={24 / (columns.md || 2)}
          lg={24 / (columns.lg || 3)}
          xl={24 / (columns.xl || 4)}
          xxl={24 / (columns.xxl || 4)}
          className="responsive-grid-item"
        >
          {child}
        </Col>
      ))}
    </Row>
  );
};

export default ResponsiveGrid;