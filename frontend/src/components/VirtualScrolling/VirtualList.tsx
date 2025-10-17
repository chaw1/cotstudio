/**
 * 虚拟滚动列表组件
 * 优化大数据量列表的渲染性能
 * 需求: 4.1, 4.2, 4.3
 */
import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Spin } from 'antd';

interface VirtualListProps<T> {
  // 数据源
  data: T[];
  // 每项高度
  itemHeight: number;
  // 容器高度
  height: number;
  // 渲染项的函数
  renderItem: (item: T, index: number) => React.ReactNode;
  // 缓冲区大小（在可视区域外渲染的项目数）
  bufferSize?: number;
  // 加载更多的回调
  onLoadMore?: () => void;
  // 是否正在加载
  loading?: boolean;
  // 是否有更多数据
  hasMore?: boolean;
  // 滚动到底部的阈值
  threshold?: number;
  // 自定义样式
  className?: string;
  style?: React.CSSProperties;
  // 空状态渲染
  emptyRender?: () => React.ReactNode;
  // 加载状态渲染
  loadingRender?: () => React.ReactNode;
}

export function VirtualList<T>({
  data,
  itemHeight,
  height,
  renderItem,
  bufferSize = 5,
  onLoadMore,
  loading = false,
  hasMore = false,
  threshold = 100,
  className,
  style,
  emptyRender,
  loadingRender,
}: VirtualListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollElementRef = useRef<HTMLDivElement>(null);

  // 计算可视区域的项目范围
  const visibleRange = useMemo(() => {
    const containerHeight = height;
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - bufferSize);
    const endIndex = Math.min(
      data.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + bufferSize
    );

    return { startIndex, endIndex };
  }, [scrollTop, height, itemHeight, data.length, bufferSize]);

  // 可视项目
  const visibleItems = useMemo(() => {
    const { startIndex, endIndex } = visibleRange;
    return data.slice(startIndex, endIndex + 1).map((item, index) => ({
      item,
      index: startIndex + index,
    }));
  }, [data, visibleRange]);

  // 总高度
  const totalHeight = data.length * itemHeight;

  // 滚动处理
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const scrollTop = e.currentTarget.scrollTop;
    setScrollTop(scrollTop);

    // 检查是否需要加载更多
    if (onLoadMore && hasMore && !loading) {
      const scrollHeight = e.currentTarget.scrollHeight;
      const clientHeight = e.currentTarget.clientHeight;
      
      if (scrollHeight - scrollTop - clientHeight < threshold) {
        onLoadMore();
      }
    }
  }, [onLoadMore, hasMore, loading, threshold]);

  // 滚动到指定索引
  const scrollToIndex = useCallback((index: number) => {
    if (scrollElementRef.current) {
      const scrollTop = index * itemHeight;
      scrollElementRef.current.scrollTop = scrollTop;
      setScrollTop(scrollTop);
    }
  }, [itemHeight]);

  // 滚动到顶部
  const scrollToTop = useCallback(() => {
    scrollToIndex(0);
  }, [scrollToIndex]);

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    scrollToIndex(data.length - 1);
  }, [scrollToIndex, data.length]);

  // 空状态
  if (data.length === 0 && !loading) {
    return (
      <div 
        className={className}
        style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          ...style,
        }}
      >
        {emptyRender ? emptyRender() : <div>暂无数据</div>}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        height,
        overflow: 'auto',
        position: 'relative',
        ...style,
      }}
      onScroll={handleScroll}
    >
      <div
        ref={scrollElementRef}
        style={{
          height: totalHeight,
          position: 'relative',
        }}
      >
        <div
          style={{
            transform: `translateY(${visibleRange.startIndex * itemHeight}px)`,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
          }}
        >
          {visibleItems.map(({ item, index }) => (
            <div
              key={index}
              style={{
                height: itemHeight,
                overflow: 'hidden',
              }}
            >
              {renderItem(item, index)}
            </div>
          ))}
        </div>
      </div>
      
      {/* 加载更多指示器 */}
      {loading && (
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 50,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
          }}
        >
          {loadingRender ? loadingRender() : <Spin size="small" />}
        </div>
      )}
    </div>
  );
}

// 虚拟表格组件
interface VirtualTableProps<T> {
  data: T[];
  columns: Array<{
    key: string;
    title: string;
    width: number;
    render?: (value: any, record: T, index: number) => React.ReactNode;
  }>;
  rowHeight: number;
  height: number;
  bufferSize?: number;
  onLoadMore?: () => void;
  loading?: boolean;
  hasMore?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function VirtualTable<T extends Record<string, any>>({
  data,
  columns,
  rowHeight,
  height,
  bufferSize = 5,
  onLoadMore,
  loading = false,
  hasMore = false,
  className,
  style,
}: VirtualTableProps<T>) {
  const totalWidth = columns.reduce((sum, col) => sum + col.width, 0);

  const renderRow = useCallback((item: T, index: number) => (
    <div
      style={{
        display: 'flex',
        width: totalWidth,
        borderBottom: '1px solid #f0f0f0',
        alignItems: 'center',
      }}
    >
      {columns.map((column) => (
        <div
          key={column.key}
          style={{
            width: column.width,
            padding: '8px 12px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {column.render 
            ? column.render(item[column.key], item, index)
            : item[column.key]
          }
        </div>
      ))}
    </div>
  ), [columns, totalWidth]);

  return (
    <div className={className} style={style}>
      {/* 表头 */}
      <div
        style={{
          display: 'flex',
          width: totalWidth,
          backgroundColor: '#fafafa',
          borderBottom: '2px solid #f0f0f0',
          fontWeight: 'bold',
        }}
      >
        {columns.map((column) => (
          <div
            key={column.key}
            style={{
              width: column.width,
              padding: '12px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {column.title}
          </div>
        ))}
      </div>
      
      {/* 虚拟列表 */}
      <VirtualList
        data={data}
        itemHeight={rowHeight}
        height={height - 45} // 减去表头高度
        renderItem={renderRow}
        bufferSize={bufferSize}
        onLoadMore={onLoadMore}
        loading={loading}
        hasMore={hasMore}
      />
    </div>
  );
}

// 虚拟网格组件
interface VirtualGridProps<T> {
  data: T[];
  itemWidth: number;
  itemHeight: number;
  height: number;
  gap?: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  onLoadMore?: () => void;
  loading?: boolean;
  hasMore?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

export function VirtualGrid<T>({
  data,
  itemWidth,
  itemHeight,
  height,
  gap = 8,
  renderItem,
  onLoadMore,
  loading = false,
  hasMore = false,
  className,
  style,
}: VirtualGridProps<T>) {
  const [containerWidth, setContainerWidth] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // 监听容器宽度变化
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.clientWidth);
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // 计算每行可容纳的项目数
  const itemsPerRow = Math.floor((containerWidth + gap) / (itemWidth + gap));
  
  // 将数据转换为行数据
  const rowData = useMemo(() => {
    const rows: T[][] = [];
    for (let i = 0; i < data.length; i += itemsPerRow) {
      rows.push(data.slice(i, i + itemsPerRow));
    }
    return rows;
  }, [data, itemsPerRow]);

  const renderRow = useCallback((row: T[], rowIndex: number) => (
    <div
      style={{
        display: 'flex',
        gap,
        padding: `0 ${gap / 2}px`,
      }}
    >
      {row.map((item, colIndex) => (
        <div
          key={rowIndex * itemsPerRow + colIndex}
          style={{
            width: itemWidth,
            height: itemHeight,
          }}
        >
          {renderItem(item, rowIndex * itemsPerRow + colIndex)}
        </div>
      ))}
    </div>
  ), [itemWidth, itemHeight, gap, renderItem, itemsPerRow]);

  return (
    <div ref={containerRef} className={className} style={style}>
      <VirtualList
        data={rowData}
        itemHeight={itemHeight + gap}
        height={height}
        renderItem={renderRow}
        onLoadMore={onLoadMore}
        loading={loading}
        hasMore={hasMore}
      />
    </div>
  );
}

export default VirtualList;