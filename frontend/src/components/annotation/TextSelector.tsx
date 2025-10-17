import React, { useState, useEffect } from 'react';
import { Card, List, Typography, Input, Button, Space, message, Spin } from 'antd';
import { SearchOutlined, FileTextOutlined } from '@ant-design/icons';
import { Slice } from '../../types';
import api from '../../services/api';

const { Text, Paragraph } = Typography;
const { Search } = Input;

interface TextSelectorProps {
  projectId: string;
  selectedSliceId?: string | null;
  onTextSelect: (text: string) => void;
  onSliceSelect: (sliceId: string) => void;
}

const TextSelector: React.FC<TextSelectorProps> = ({
  projectId,
  selectedSliceId,
  onTextSelect,
  onSliceSelect,
}) => {
  const [slices, setSlices] = useState<Slice[]>([]);
  const [filteredSlices, setFilteredSlices] = useState<Slice[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [searchText, setSearchText] = useState<string>('');
  const [selectedText, setSelectedText] = useState<string>('');

  // 加载切片数据
  const loadSlices = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/ocr/project/${projectId}/slices`);
      // 后端返回 ResponseModel 包装的数据，需要取 data 字段
      const slicesData = response.data || [];
      setSlices(slicesData);
      setFilteredSlices(slicesData);
    } catch (error) {
      message.error('加载切片数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 搜索切片
  const handleSearch = (value: string) => {
    setSearchText(value);
    if (!value.trim()) {
      setFilteredSlices(slices);
    } else {
      const filtered = slices.filter(slice =>
        slice.content.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredSlices(filtered);
    }
  };

  // 选择切片
  const handleSliceSelect = (slice: Slice) => {
    onSliceSelect(slice.id);
    setSelectedText(''); // 清空之前选中的文本
  };

  // 处理文本选择
  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      const text = selection.toString().trim();
      setSelectedText(text);
      onTextSelect(text);
      message.success('文本选择成功');
    }
  };

  // 获取切片类型图标
  const getSliceTypeIcon = (type: string) => {
    switch (type) {
      case 'paragraph':
        return <FileTextOutlined style={{ color: '#1890ff' }} />;
      case 'image':
        return <FileTextOutlined style={{ color: '#52c41a' }} />;
      case 'table':
        return <FileTextOutlined style={{ color: '#faad14' }} />;
      default:
        return <FileTextOutlined />;
    }
  };

  // 获取切片类型标签
  const getSliceTypeLabel = (type: string) => {
    switch (type) {
      case 'paragraph':
        return '段落';
      case 'image':
        return '图片';
      case 'table':
        return '表格';
      default:
        return '未知';
    }
  };

  useEffect(() => {
    if (projectId) {
      loadSlices();
    }
  }, [projectId]);

  return (
    <div>
      <div style={{ marginBottom: '16px' }}>
        <Search
          placeholder="搜索切片内容..."
          allowClear
          onSearch={handleSearch}
          onChange={(e) => handleSearch(e.target.value)}
          style={{ marginBottom: '8px' }}
        />
        <Text type="secondary" style={{ fontSize: '12px' }}>
          点击切片选择，然后在右侧内容中拖拽选择文本
        </Text>
      </div>

      <Spin spinning={loading}>
        <List
          size="small"
          dataSource={filteredSlices}
          renderItem={(slice) => (
            <List.Item
              key={slice.id}
              style={{
                cursor: 'pointer',
                backgroundColor: selectedSliceId === slice.id ? '#e6f7ff' : 'transparent',
                border: selectedSliceId === slice.id ? '1px solid #1890ff' : '1px solid transparent',
                borderRadius: '4px',
                marginBottom: '4px',
                padding: '8px',
              }}
              onClick={() => handleSliceSelect(slice)}
            >
              <List.Item.Meta
                avatar={getSliceTypeIcon(slice.sliceType)}
                title={
                  <Space>
                    <Text strong style={{ fontSize: '12px' }}>
                      {getSliceTypeLabel(slice.sliceType)}
                    </Text>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      第{slice.pageNumber}页
                    </Text>
                  </Space>
                }
                description={
                  <Paragraph
                    ellipsis={{ rows: 2, expandable: false }}
                    style={{ margin: 0, fontSize: '12px' }}
                  >
                    {slice.content}
                  </Paragraph>
                }
              />
            </List.Item>
          )}
          locale={{ emptyText: '暂无切片数据' }}
        />
      </Spin>

      {selectedSliceId && (
        <Card size="small" style={{ marginTop: '16px' }}>
          <Text strong style={{ fontSize: '12px' }}>当前选中切片:</Text>
          <div
            style={{
              marginTop: '8px',
              padding: '8px',
              background: '#f9f9f9',
              borderRadius: '4px',
              maxHeight: '200px',
              overflow: 'auto',
              userSelect: 'text',
              cursor: 'text',
            }}
            onMouseUp={handleTextSelection}
          >
            <Text style={{ fontSize: '12px' }}>
              {slices.find(s => s.id === selectedSliceId)?.content || ''}
            </Text>
          </div>
          <div style={{ marginTop: '8px' }}>
            <Text type="secondary" style={{ fontSize: '11px' }}>
              在上方文本中拖拽选择需要标注的部分
            </Text>
          </div>
          {selectedText && (
            <div style={{ marginTop: '8px' }}>
              <Text strong style={{ fontSize: '12px' }}>已选择文本:</Text>
              <div style={{
                marginTop: '4px',
                padding: '4px 8px',
                background: '#fff2e8',
                border: '1px solid #ffb366',
                borderRadius: '4px',
              }}>
                <Text style={{ fontSize: '12px' }}>{selectedText}</Text>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default TextSelector;