import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Input, 
  Select, 
  Space, 
  Typography, 
  Checkbox, 
  Slider, 
  Button,
  Divider,
  Tag,
  AutoComplete
} from 'antd';
import { SearchOutlined, ClearOutlined, FilterOutlined } from '@ant-design/icons';
import { KGEntity, KGRelation } from '../../types';
import { FilterOptions } from './types';

const { Title, Text } = Typography;
const { Option } = Select;
const CheckboxGroup = Checkbox.Group;

interface KGSearchPanelProps {
  onSearch: (query: string) => void;
  onFilter: (options: FilterOptions) => void;
  filterOptions: FilterOptions;
  entities: KGEntity[];
  relations: KGRelation[];
}

const KGSearchPanel: React.FC<KGSearchPanelProps> = ({
  onSearch,
  onFilter,
  filterOptions,
  entities,
  relations
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([]);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // 获取所有实体类型
  const entityTypes = Array.from(new Set(entities.map(e => e.type))).sort();
  
  // 获取所有关系类型
  const relationTypes = Array.from(new Set(relations.map(r => r.type))).sort();

  // 生成搜索建议 - 使用useCallback避免无限循环
  useEffect(() => {
    if (searchQuery.length > 1) {
      const suggestions = [
        ...entities
          .filter(e => e.label.toLowerCase().includes(searchQuery.toLowerCase()))
          .map(e => e.label)
          .slice(0, 5),
        ...entityTypes
          .filter(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
          .slice(0, 3)
      ];
      setSearchSuggestions([...new Set(suggestions)]);
    } else {
      setSearchSuggestions([]);
    }
  }, [searchQuery, entities.length, entityTypes.length]); // 只依赖长度，避免引用变化

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    onSearch(value);
  };

  // 处理过滤器变化
  const handleFilterChange = (key: keyof FilterOptions, value: any) => {
    const newOptions = { ...filterOptions, [key]: value };
    onFilter(newOptions);
  };

  // 清除所有过滤器
  const clearFilters = () => {
    const defaultOptions: FilterOptions = {
      entityTypes: [],
      relationTypes: [],
      minConnections: 0,
      maxNodes: 100,
      searchQuery: ''
    };
    setSearchQuery('');
    onFilter(defaultOptions);
    onSearch('');
  };

  // 获取活跃过滤器数量
  const getActiveFiltersCount = () => {
    let count = 0;
    if (filterOptions.entityTypes.length > 0) count++;
    if (filterOptions.relationTypes.length > 0) count++;
    if (filterOptions.minConnections > 0) count++;
    if (filterOptions.maxNodes < 100) count++;
    if (filterOptions.searchQuery) count++;
    return count;
  };

  return (
    <Card 
      title={
        <Space>
          <SearchOutlined />
          搜索与过滤
          {getActiveFiltersCount() > 0 && (
            <Tag color="blue">{getActiveFiltersCount()} 个过滤器</Tag>
          )}
        </Space>
      } 
      size="small" 
      style={{ marginBottom: 16 }}
      extra={
        <Button 
          type="text" 
          size="small" 
          icon={<ClearOutlined />}
          onClick={clearFilters}
          title="清除所有过滤器"
        />
      }
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 搜索框 */}
        <div>
          <Text type="secondary" style={{ fontSize: '12px' }}>搜索节点</Text>
          <AutoComplete
            value={searchQuery}
            options={searchSuggestions.map(s => ({ value: s }))}
            onSearch={setSearchQuery}
            onSelect={handleSearch}
            style={{ width: '100%' }}
          >
            <Input
              placeholder="输入实体名称或类型..."
              suffix={<SearchOutlined />}
              onPressEnter={(e) => handleSearch((e.target as HTMLInputElement).value)}
              allowClear
            />
          </AutoComplete>
        </div>

        <Divider style={{ margin: '12px 0' }} />

        {/* 快速过滤 */}
        <div>
          <Space>
            <Button 
              size="small" 
              type={showAdvancedFilters ? 'primary' : 'default'}
              icon={<FilterOutlined />}
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            >
              高级过滤
            </Button>
          </Space>
        </div>

        {/* 实体类型过滤 */}
        <div>
          <Text type="secondary" style={{ fontSize: '12px' }}>实体类型</Text>
          <Select
            mode="multiple"
            value={filterOptions.entityTypes}
            onChange={(value) => handleFilterChange('entityTypes', value)}
            placeholder="选择实体类型"
            style={{ width: '100%' }}
            maxTagCount={3}
            maxTagTextLength={10}
            showSearch
            filterOption={(input, option) =>
              (option?.children as any)?.[0]?.props?.children?.toLowerCase().includes(input.toLowerCase())
            }
          >
            {entityTypes.map(type => (
              <Option key={type} value={type}>
                <Space>
                  <span>{type}</span>
                  <Text type="secondary" style={{ fontSize: '11px' }}>
                    ({entities.filter(e => e.type === type).length})
                  </Text>
                </Space>
              </Option>
            ))}
          </Select>
        </div>

        {/* 关系类型过滤 */}
        <div>
          <Text type="secondary" style={{ fontSize: '12px' }}>关系类型</Text>
          <Select
            mode="multiple"
            value={filterOptions.relationTypes}
            onChange={(value) => handleFilterChange('relationTypes', value)}
            placeholder="选择关系类型"
            style={{ width: '100%' }}
            maxTagCount={3}
            maxTagTextLength={10}
            showSearch
            filterOption={(input, option) =>
              (option?.children as any)?.[0]?.props?.children?.toLowerCase().includes(input.toLowerCase())
            }
          >
            {relationTypes.map(type => (
              <Option key={type} value={type}>
                <Space>
                  <span>{type}</span>
                  <Text type="secondary" style={{ fontSize: '11px' }}>
                    ({relations.filter(r => r.type === type).length})
                  </Text>
                </Space>
              </Option>
            ))}
          </Select>
        </div>

        {/* 高级过滤器 */}
        {showAdvancedFilters && (
          <>
            <Divider style={{ margin: '12px 0' }} />
            
            {/* 最小连接数 */}
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                最小连接数: {filterOptions.minConnections}
              </Text>
              <Slider
                min={0}
                max={10}
                value={filterOptions.minConnections}
                onChange={(value) => handleFilterChange('minConnections', value)}
                marks={{
                  0: '0',
                  2: '2',
                  5: '5',
                  10: '10+'
                }}
                tooltip={{ formatter: (value) => `至少 ${value} 个连接` }}
              />
            </div>

            {/* 最大节点数 */}
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                最大显示节点: {filterOptions.maxNodes}
              </Text>
              <Slider
                min={10}
                max={500}
                value={filterOptions.maxNodes}
                onChange={(value) => handleFilterChange('maxNodes', value)}
                marks={{
                  10: '10',
                  50: '50',
                  100: '100',
                  200: '200',
                  500: '500'
                }}
                tooltip={{ formatter: (value) => `最多 ${value} 个节点` }}
              />
            </div>
          </>
        )}

        {/* 预设过滤器 */}
        <div>
          <Text type="secondary" style={{ fontSize: '12px' }}>快速过滤</Text>
          <Space wrap style={{ marginTop: '4px' }}>
            <Button 
              size="small" 
              type="default"
              onClick={() => handleFilterChange('entityTypes', ['Person'])}
            >
              人物
            </Button>
            <Button 
              size="small" 
              type="default"
              onClick={() => handleFilterChange('entityTypes', ['Organization'])}
            >
              组织
            </Button>
            <Button 
              size="small" 
              type="default"
              onClick={() => handleFilterChange('entityTypes', ['Concept'])}
            >
              概念
            </Button>
            <Button 
              size="small" 
              type="default"
              onClick={() => handleFilterChange('minConnections', 3)}
            >
              核心节点
            </Button>
          </Space>
        </div>

        {/* 当前过滤状态 */}
        {getActiveFiltersCount() > 0 && (
          <>
            <Divider style={{ margin: '12px 0' }} />
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>当前过滤器</Text>
              <Space wrap style={{ marginTop: '4px' }}>
                {filterOptions.entityTypes.map(type => (
                  <Tag 
                    key={type} 
                    closable 
                    onClose={() => {
                      const newTypes = filterOptions.entityTypes.filter(t => t !== type);
                      handleFilterChange('entityTypes', newTypes);
                    }}
                  >
                    {type}
                  </Tag>
                ))}
                {filterOptions.relationTypes.map(type => (
                  <Tag 
                    key={type} 
                    color="blue"
                    closable 
                    onClose={() => {
                      const newTypes = filterOptions.relationTypes.filter(t => t !== type);
                      handleFilterChange('relationTypes', newTypes);
                    }}
                  >
                    {type}
                  </Tag>
                ))}
                {filterOptions.minConnections > 0 && (
                  <Tag 
                    color="green"
                    closable 
                    onClose={() => handleFilterChange('minConnections', 0)}
                  >
                    连接≥{filterOptions.minConnections}
                  </Tag>
                )}
              </Space>
            </div>
          </>
        )}
      </Space>
    </Card>
  );
};

export default KGSearchPanel;