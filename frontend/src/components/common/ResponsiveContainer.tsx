import React from 'react';
import { useResponsiveBreakpoint, createResponsiveStyles } from '../../hooks/useResponsiveBreakpoint';

interface ResponsiveContainerProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  maxWidth?: number | string;
  padding?: boolean;
  center?: boolean;
}

/**
 * 响应式容器组件 - 自动适配不同屏幕尺寸
 */
export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  className = '',
  style = {},
  maxWidth,
  padding = true,
  center = true
}) => {
  const { breakpoint, isMobile } = useResponsiveBreakpoint();
  const responsiveStyles = createResponsiveStyles(breakpoint, isMobile);

  const containerStyle: React.CSSProperties = {
    width: '100%',
    ...(maxWidth && { maxWidth }),
    ...(center && { margin: '0 auto' }),
    ...(padding && responsiveStyles.container),
    ...style
  };

  return (
    <div className={className} style={containerStyle}>
      {children}
    </div>
  );
};

interface ResponsiveGridProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  gap?: number | string;
  minItemWidth?: number;
  maxCols?: number;
}

/**
 * 响应式网格组件 - 自动调整列数
 */
export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  className = '',
  style = {},
  gap = 16,
  minItemWidth = 280,
  maxCols = 6
}) => {
  const { screenWidth, getGridCols } = useResponsiveBreakpoint();
  
  // 计算最优列数
  const calculateCols = () => {
    const availableWidth = screenWidth - 48; // 减去容器padding
    const itemWidthWithGap = minItemWidth + (typeof gap === 'number' ? gap : 16);
    const calculatedCols = Math.floor(availableWidth / itemWidthWithGap);
    const responsiveCols = getGridCols();
    
    return Math.min(calculatedCols, responsiveCols, maxCols);
  };

  const cols = calculateCols();

  const gridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: `repeat(${cols}, 1fr)`,
    gap: gap,
    width: '100%',
    ...style
  };

  return (
    <div className={className} style={gridStyle}>
      {children}
    </div>
  );
};

interface ResponsiveTextProps {
  children: React.ReactNode;
  variant?: 'title' | 'body' | 'caption';
  className?: string;
  style?: React.CSSProperties;
}

/**
 * 响应式文本组件 - 自动调整字体大小
 */
export const ResponsiveText: React.FC<ResponsiveTextProps> = ({
  children,
  variant = 'body',
  className = '',
  style = {}
}) => {
  const { breakpoint, isMobile } = useResponsiveBreakpoint();
  const responsiveStyles = createResponsiveStyles(breakpoint, isMobile);

  const textStyle: React.CSSProperties = {
    ...responsiveStyles.text[variant],
    ...style
  };

  const Tag = variant === 'title' ? 'h2' : variant === 'caption' ? 'small' : 'p';

  return (
    <Tag className={className} style={textStyle}>
      {children}
    </Tag>
  );
};

interface ResponsiveSpacerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  direction?: 'horizontal' | 'vertical';
}

/**
 * 响应式间距组件 - 自动调整间距大小
 */
export const ResponsiveSpacer: React.FC<ResponsiveSpacerProps> = ({
  size = 'md',
  direction = 'vertical'
}) => {
  const { getSpacing } = useResponsiveBreakpoint();
  const spacing = getSpacing(size);

  const spacerStyle: React.CSSProperties = {
    [direction === 'vertical' ? 'height' : 'width']: `${spacing}px`,
    [direction === 'vertical' ? 'width' : 'height']: '100%',
    flexShrink: 0
  };

  return <div style={spacerStyle} />;
};

interface ResponsiveShowProps {
  children: React.ReactNode;
  breakpoint?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl';
  above?: boolean;
  below?: boolean;
  only?: boolean;
}

/**
 * 响应式显示组件 - 根据断点控制显示/隐藏
 */
export const ResponsiveShow: React.FC<ResponsiveShowProps> = ({
  children,
  breakpoint: targetBreakpoint,
  above = false,
  below = false,
  only = false
}) => {
  const { breakpoint: currentBreakpoint } = useResponsiveBreakpoint();
  
  if (!targetBreakpoint) {
    return <>{children}</>;
  }

  const breakpointOrder = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl'];
  const currentIndex = breakpointOrder.indexOf(currentBreakpoint);
  const targetIndex = breakpointOrder.indexOf(targetBreakpoint);

  let shouldShow = false;

  if (only) {
    shouldShow = currentBreakpoint === targetBreakpoint;
  } else if (above) {
    shouldShow = currentIndex >= targetIndex;
  } else if (below) {
    shouldShow = currentIndex <= targetIndex;
  } else {
    shouldShow = currentIndex >= targetIndex;
  }

  return shouldShow ? <>{children}</> : null;
};

// 导出所有组件
export default {
  Container: ResponsiveContainer,
  Grid: ResponsiveGrid,
  Text: ResponsiveText,
  Spacer: ResponsiveSpacer,
  Show: ResponsiveShow
};