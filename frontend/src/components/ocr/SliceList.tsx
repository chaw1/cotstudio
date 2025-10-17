import React, { useState, useEffect } from 'react';
import {
  Card,
  List,
  Typography,
  Space,
  Tag,
  Button,
  Input,
  Select,
  Pagination,
  Empty,
  Tooltip,
  Badge,
  Divider,
} from 'antd';
import {
  FileTextOutlined,
  PictureOutlined,
  TableOutlined,
  EyeOutlined,
  SearchOutlined,
  FilterOutlined,
} from '@ant-design/icons';
import { Slice } from '../../types';

const { Text, Paragraph } = Typography;
const { Search } = Input;
const { Option } = Select;

interface SliceListProps {
  fileId: string;
  slices: Slice[];
  loading?: boolean;
  onSliceSelect: (slice: Slice) => void;
  onSliceHighlight?: (slice: Slice) => void;
  selectedSliceId?: string;
}

const SliceList: React.FC<SliceListProps> = ({
  fileId,
  slices,
  loading = false,
  onSliceSelect,
  onSliceHighlight,
  selectedSliceId,
}) => {
  const [filteredSlices, setFilteredSlices] = useState<Slice[]>(slices);
  const [searchText, setSearchText] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // 更新过滤后的切片列表
  useEffect(() => {
    let filtered = [...slices];

    // 按类型过滤
    if (filterType !== 'all') {
      filtered = filtered.filter(slice => slice.sliceType === filterType);
    }

    // 按搜索文本过滤
    if (searchText.trim()) {
      const searchLower = searchText.toLowerCase();
      filtered = filtered.filter(slice =>
        slice.content.toLowerCase().includes(searchLower)
      );
    }

    setFilteredSlices(filtered);
    setCurrentPage(1); // 重置到第一页
  }, [slices, searchText, filterType]);

  // 获取切片类型图标
  const getSliceTypeIcon = (type: string) => {
    switch (type) {
      case 'paragraph':
        return <FileTextOutlined style={{ color: '#1677ff' }} />;
      case 'image':
        return <PictureOutlined style={{ color: '#52c41a' }} />;
      case 'table':
        return <TableOutlined style={{ color: '#faad14' }} />;
      default:
        return <FileTextOutlined />;
    }
  };

  // 获取切片类型标签
  const getSliceTypeTag = (type: string) => {
    const typeMap = {
      paragraph: { text: '段落', color: 'blue' },
      image: { text: '图像', color: 'green' },
      table: { text: '表格', color: 'orange' },
    };
    const config = typeMap[type as keyof typeof typeMap] || { text: type, color: 'default' };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 截断文本
  const truncateText = (text: string, maxLength: number = 200) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  // 高亮搜索文本
  const highlightSearchText = (text: string, searchText: string) => {
    if (!searchText.trim()) return text;
    
    const regex = new RegExp(`(${searchText})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} style={{ backgroundColor: '#fff566', padding: 0 }}>
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  // 获取当前页的切片
  const getCurrentPageSlices = () => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filteredSlices.slice(startIndex, endIndex);
  };

  // 统计信息
  const getStatistics = () => {
    const total = slices.length;
    const paragraphs = slices.filter(s => s.sliceType === 'paragraph').length;
    const images = slices.filter(s => s.sliceType === 'image').length;
    const tables = slices.filter(s => s.sliceType === 'table').length;
    
    return { total, paragraphs, images, tables };
  };

  const stats = getStatistics();

  return (
    <Card
      title={
        <Space>
          <FileTextOutlined />
          <span>文档切片</span>
          <Badge count={filteredSlices.length} showZero />
        </Space>
      }
      extra={
        <Space>
          <Text type="secondary">
            共 {stats.total} 个切片
          </Text>
        </Space>
      }
    >
      {/* 统计信息 */}
      <div style={{ marginBottom: 16 }}>
        <Space wrap>
          <Tag icon={<FileTextOutlined />} color="blue">
            段落: {stats.paragraphs}
          </Tag>
          <Tag icon={<PictureOutlined />} color="green">
            图像: {stats.images}
          </Tag>
          <Tag icon={<TableOutlined />} color="orange">
            表格: {stats.tables}
          </Tag>
        </Space>
      </div>

      {/* 搜索和过滤 */}
      <div style={{ marginBottom: 16 }}>
        <Space style={{ width: '100%' }} direction="vertical">
          <div style={{ display: 'flex', gap: 8 }}>
            <Search
              placeholder="搜索切片内容..."
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ flex: 1 }}
              prefix={<SearchOutlined />}
            />
            <Select
              value={filterType}
              onChange={setFilterType}
              style={{ width: 120 }}
              prefix={<FilterOutlined />}
            >
              <Option value="all">全部类型</Option>
              <Option value="paragraph">段落</Option>
              <Option value="image">图像</Option>
              <Option value="table">表格</Option>
            </Select>
          </div>
        </Space>
      </div>

      <Divider />

      {/* 切片列表 */}
      {filteredSlices.length === 0 ? (
        <Empty
          description={
            searchText || filterType !== 'all'
              ? '没有找到匹配的切片'
              : '暂无切片数据'
          }
        />
      ) : (
        <>
          <List
            loading={loading}
            dataSource={getCurrentPageSlices()}
            renderItem={(slice) => (
              <List.Item
                key={slice.id}
                className={selectedSliceId === slice.id ? 'selected-slice' : ''}
                style={{
                  backgroundColor: selectedSliceId === slice.id ? '#e6f4ff' : 'transparent',
                  borderRadius: 8,
                  marginBottom: 8,
                  padding: 16,
                  border: selectedSliceId === slice.id ? '1px solid #1677ff' : '1px solid #f0f0f0',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
                onClick={() => onSliceSelect(slice)}
                onMouseEnter={() => onSliceHighlight?.(slice)}
              >
                <List.Item.Meta
                  avatar={getSliceTypeIcon(slice.sliceType)}
                  title={
                    <Space>
                      {getSliceTypeTag(slice.sliceType)}
                      <Text type="secondary">
                        第 {slice.pageNumber} 页
                      </Text>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        位置: {slice.startOffset}-{slice.endOffset}
                      </Text>
                    </Space>
                  }
                  description={
                    <div>
                      <Paragraph
                        style={{ marginBottom: 8 }}
                        ellipsis={{ rows: 3, expandable: false }}
                      >
                        {highlightSearchText(slice.content, searchText)}
                      </Paragraph>
                      <Space>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          创建时间: {new Date(slice.createdAt).toLocaleString('zh-CN')}
                        </Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          长度: {slice.content.length} 字符
                        </Text>
                      </Space>
                    </div>
                  }
                />
                <div>
                  <Tooltip title="查看详情">
                    <Button
                      type="text"
                      icon={<EyeOutlined />}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSliceSelect(slice);
                      }}
                    />
                  </Tooltip>
                </div>
              </List.Item>
            )}
          />

          {/* 分页 */}
          {filteredSlices.length > pageSize && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Pagination
                current={currentPage}
                pageSize={pageSize}
                total={filteredSlices.length}
                onChange={setCurrentPage}
                onShowSizeChange={(current, size) => {
                  setCurrentPage(1);
                  setPageSize(size);
                }}
                showSizeChanger
                showQuickJumper
                showTotal={(total, range) =>
                  `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                }
                pageSizeOptions={['10', '20', '50', '100']}
              />
            </div>
          )}
        </>
      )}

      <style>{`
        .selected-slice {
          box-shadow: 0 2px 8px rgba(22, 119, 255, 0.15);
        }
        
        .selected-slice:hover {
          box-shadow: 0 4px 12px rgba(22, 119, 255, 0.25);
        }
        
        .ant-list-item:hover {
          background-color: #f5f5f5 !important;
        }
        
        .selected-slice:hover {
          background-color: #e6f4ff !important;
        }
      `}</style>
    </Card>
  );
};

export default SliceList;