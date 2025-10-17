/**
 * 导出格式选择器组件
 */
import React from 'react';
import { Card, Radio, Typography, Space } from 'antd';
import { FileTextOutlined, FileMarkdownOutlined, FileOutlined, FilePdfOutlined } from '@ant-design/icons';
import { ExportFormat } from '../../types/export';
import exportService from '../../services/exportService';

const { Title, Text } = Typography;

interface FormatSelectorProps {
  selectedFormat: ExportFormat;
  onFormatChange: (format: ExportFormat) => void;
}

const FormatSelector: React.FC<FormatSelectorProps> = ({
  selectedFormat,
  onFormatChange
}) => {
  const formatOptions = [
    {
      value: ExportFormat.JSON,
      label: 'JSON 格式',
      icon: <FileTextOutlined />,
      description: '结构化数据格式，适合程序处理和数据分析'
    },
    {
      value: ExportFormat.MARKDOWN,
      label: 'Markdown 格式',
      icon: <FileMarkdownOutlined />,
      description: '易读的文本格式，适合文档编写和展示'
    },
    {
      value: ExportFormat.LATEX,
      label: 'LaTeX 格式',
      icon: <FilePdfOutlined />,
      description: '学术论文格式，适合生成高质量的PDF文档'
    },
    {
      value: ExportFormat.TXT,
      label: '纯文本格式',
      icon: <FileOutlined />,
      description: '简单的文本格式，兼容性最好'
    }
  ];

  return (
    <Card title="选择导出格式" size="small">
      <Radio.Group
        value={selectedFormat}
        onChange={(e) => onFormatChange(e.target.value)}
        style={{ width: '100%' }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          {formatOptions.map(option => (
            <Radio key={option.value} value={option.value} style={{ width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                <div style={{ fontSize: '16px', marginTop: '2px' }}>
                  {option.icon}
                </div>
                <div>
                  <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                    {option.label}
                  </div>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {option.description}
                  </Text>
                </div>
              </div>
            </Radio>
          ))}
        </Space>
      </Radio.Group>

      <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f0f8ff', borderRadius: '6px', border: '1px solid #d6e4ff' }}>
        <Text style={{ fontSize: '12px', color: '#1890ff' }}>
          <strong>提示：</strong>
          {selectedFormat === ExportFormat.JSON && '选择JSON格式可以保留完整的数据结构，便于后续处理。'}
          {selectedFormat === ExportFormat.MARKDOWN && '选择Markdown格式可以生成易读的文档，支持在线预览。'}
          {selectedFormat === ExportFormat.LATEX && '选择LaTeX格式可以生成专业的学术文档，需要LaTeX编译器处理。'}
          {selectedFormat === ExportFormat.TXT && '选择纯文本格式可以在任何文本编辑器中打开，但会丢失格式信息。'}
        </Text>
      </div>
    </Card>
  );
};

export default FormatSelector;