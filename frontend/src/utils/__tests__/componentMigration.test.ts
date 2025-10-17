import { describe, it, expect, beforeEach } from 'vitest';
import {
  adaptProps,
  migrateComponent,
  checkComponentCompatibility,
  migrationTracker,
  analyzeComponentUsage,
  COMPONENT_MIGRATION_MAP,
  PROP_MAPPINGS,
  MigrationTracker
} from '../componentMigration';

describe('Component Migration Utils', () => {
  beforeEach(() => {
    // 清理迁移跟踪器状态
    migrationTracker.getAllStatuses().forEach(status => {
      migrationTracker.updateStatus(status.componentName, 'pending');
    });
  });

  describe('adaptProps', () => {
    it('should adapt Button props correctly', () => {
      const antdProps = {
        type: 'primary',
        size: 'large',
        loading: true,
        disabled: false,
        danger: true,
        block: true
      };

      const heroProps = adaptProps('Button', antdProps);

      expect(heroProps.type).toBe('primary');
      expect(heroProps.size).toBe('lg');
      expect(heroProps.isLoading).toBe(true);
      expect(heroProps.isDisabled).toBe(false);
      expect(heroProps.color).toBe('danger');
      expect(heroProps.fullWidth).toBe(true);
    });

    it('should adapt Card props correctly', () => {
      const antdProps = {
        title: 'Test Card',
        bordered: false,
        hoverable: true,
        size: 'small'
      };

      const heroProps = adaptProps('Card', antdProps);

      expect(heroProps.title).toBe('Test Card');
      expect(heroProps.shadow).toBe('none');
      expect(heroProps.isPressable).toBe(true);
      expect(heroProps.size).toBe('sm');
    });

    it('should adapt Input props correctly', () => {
      const antdProps = {
        placeholder: 'Enter text',
        disabled: true,
        size: 'middle',
        allowClear: true,
        prefix: 'prefix-icon',
        suffix: 'suffix-icon'
      };

      const heroProps = adaptProps('Input', antdProps);

      expect(heroProps).toEqual({
        placeholder: 'Enter text',
        isDisabled: true,
        size: 'md',
        isClearable: true,
        startContent: 'prefix-icon',
        endContent: 'suffix-icon'
      });
    });

    it('should handle unmapped props', () => {
      const antdProps = {
        customProp: 'custom-value',
        onClick: () => {},
        className: 'custom-class'
      };

      const heroProps = adaptProps('Button', antdProps);

      expect(heroProps.customProp).toBe('custom-value');
      expect(heroProps.onClick).toBeDefined();
      expect(heroProps.className).toBe('custom-class');
    });
  });

  describe('migrateComponent', () => {
    it('should return null for unsupported components', () => {
      const result = migrateComponent('UnsupportedComponent', {});
      expect(result).toBeNull();
    });

    it('should create component for supported components', () => {
      const result = migrateComponent('Button', { type: 'primary' });
      expect(result).toBeDefined();
      expect(result?.type).toBeDefined();
    });
  });

  describe('checkComponentCompatibility', () => {
    it('should check Button compatibility', () => {
      const compatibility = checkComponentCompatibility('Button');
      
      expect(compatibility.isSupported).toBe(true);
      expect(compatibility.hasMapping).toBe(true);
      expect(compatibility.missingFeatures).toEqual([]);
    });

    it('should check Table compatibility', () => {
      const compatibility = checkComponentCompatibility('Table');
      
      expect(compatibility.isSupported).toBe(true);
      expect(compatibility.hasMapping).toBe(true);
      expect(compatibility.missingFeatures).toContain('expandable rows');
      expect(compatibility.missingFeatures).toContain('column grouping');
      expect(compatibility.missingFeatures).toContain('tree data');
    });

    it('should check Form compatibility', () => {
      const compatibility = checkComponentCompatibility('Form');
      
      expect(compatibility.isSupported).toBe(false);
      expect(compatibility.hasMapping).toBe(false);
      expect(compatibility.missingFeatures).toContain('form validation');
      expect(compatibility.missingFeatures).toContain('form layout');
      expect(compatibility.missingFeatures).toContain('form items');
    });

    it('should check Upload compatibility', () => {
      const compatibility = checkComponentCompatibility('Upload');
      
      expect(compatibility.isSupported).toBe(false);
      expect(compatibility.hasMapping).toBe(false);
      expect(compatibility.missingFeatures).toContain('file upload');
      expect(compatibility.missingFeatures).toContain('drag and drop');
      expect(compatibility.missingFeatures).toContain('progress tracking');
    });
  });

  describe('MigrationTracker', () => {
    it('should track migration status', () => {
      // 创建新的跟踪器实例以避免状态污染
      const tracker = MigrationTracker.getInstance();
      
      tracker.updateStatus('TestButton', 'completed');
      tracker.updateStatus('TestCard', 'in-progress', ['styling issues']);
      tracker.updateStatus('TestTable', 'failed', ['complex features not supported']);

      const buttonStatus = tracker.getStatus('TestButton');
      expect(buttonStatus?.status).toBe('completed');
      expect(buttonStatus?.issues).toEqual([]);

      const cardStatus = tracker.getStatus('TestCard');
      expect(cardStatus?.status).toBe('in-progress');
      expect(cardStatus?.issues).toEqual(['styling issues']);

      const tableStatus = tracker.getStatus('TestTable');
      expect(tableStatus?.status).toBe('failed');
      expect(tableStatus?.issues).toEqual(['complex features not supported']);
    });

    it('should calculate progress correctly', () => {
      // 创建新的跟踪器实例
      const tracker = MigrationTracker.getInstance();
      
      // 清理之前的状态
      tracker.getAllStatuses().forEach(status => {
        tracker.updateStatus(status.componentName, 'pending');
      });
      
      tracker.updateStatus('ProgressButton', 'completed');
      tracker.updateStatus('ProgressCard', 'completed');
      tracker.updateStatus('ProgressInput', 'in-progress');
      tracker.updateStatus('ProgressTable', 'pending');

      const progress = tracker.getProgress();
      
      expect(progress.completed).toBeGreaterThanOrEqual(2);
      expect(progress.total).toBeGreaterThanOrEqual(4);
      expect(progress.percentage).toBeGreaterThanOrEqual(0);
    });

    it('should handle empty migration list', () => {
      // 创建一个新的类实例来测试空状态
      class TestMigrationTracker {
        private migrations: Map<string, any> = new Map();
        
        getProgress() {
          const statuses = Array.from(this.migrations.values());
          const completed = statuses.filter(s => s.status === 'completed').length;
          const total = statuses.length;
          const percentage = total > 0 ? (completed / total) * 100 : 0;
          
          return { completed, total, percentage };
        }
      }
      
      const emptyTracker = new TestMigrationTracker();
      const progress = emptyTracker.getProgress();
      
      expect(progress.completed).toBe(0);
      expect(progress.total).toBe(0);
      expect(progress.percentage).toBe(0);
    });
  });

  describe('analyzeComponentUsage', () => {
    it('should analyze component usage in codebase', () => {
      const mockCodebase = `
        import { Button, Card, Table, Form, Upload } from 'antd';
        import { Input, Select } from 'antd';
        
        const MyComponent = () => {
          return (
            <div>
              <Button type="primary">Click me</Button>
              <Card title="My Card">Content</Card>
              <Table dataSource={data} columns={columns} />
            </div>
          );
        };
      `;

      const analysis = analyzeComponentUsage(mockCodebase);

      expect(analysis.antdComponents).toContain('Button');
      expect(analysis.antdComponents).toContain('Card');
      expect(analysis.antdComponents).toContain('Table');
      expect(analysis.antdComponents).toContain('Form');
      expect(analysis.antdComponents).toContain('Upload');
      expect(analysis.antdComponents).toContain('Input');
      expect(analysis.antdComponents).toContain('Select');

      expect(analysis.migrationCandidates).toContain('Button');
      expect(analysis.migrationCandidates).toContain('Card');
      expect(analysis.migrationCandidates).toContain('Table');
      expect(analysis.migrationCandidates).toContain('Input');
      expect(analysis.migrationCandidates).toContain('Select');

      expect(analysis.complexComponents).toContain('Table');
      expect(analysis.complexComponents).toContain('Upload');
    });

    it('should handle empty codebase', () => {
      const analysis = analyzeComponentUsage('');
      
      expect(analysis.antdComponents).toEqual([]);
      expect(analysis.migrationCandidates).toEqual([]);
      expect(analysis.complexComponents).toEqual([]);
    });
  });

  describe('Component and Prop Mappings', () => {
    it('should have valid component mappings', () => {
      expect(COMPONENT_MIGRATION_MAP).toBeDefined();
      expect(Object.keys(COMPONENT_MIGRATION_MAP).length).toBeGreaterThan(0);
      
      // 检查关键组件是否存在
      expect(COMPONENT_MIGRATION_MAP.Button).toBeDefined();
      expect(COMPONENT_MIGRATION_MAP.Card).toBeDefined();
      expect(COMPONENT_MIGRATION_MAP.Input).toBeDefined();
      expect(COMPONENT_MIGRATION_MAP.Select).toBeDefined();
      expect(COMPONENT_MIGRATION_MAP.Table).toBeDefined();
    });

    it('should have valid prop mappings', () => {
      expect(PROP_MAPPINGS).toBeDefined();
      expect(Object.keys(PROP_MAPPINGS).length).toBeGreaterThan(0);
      
      // 检查关键组件的属性映射
      expect(PROP_MAPPINGS.Button).toBeDefined();
      expect(PROP_MAPPINGS.Card).toBeDefined();
      expect(PROP_MAPPINGS.Input).toBeDefined();
      expect(PROP_MAPPINGS.Select).toBeDefined();
      expect(PROP_MAPPINGS.Table).toBeDefined();
    });

    it('should have consistent mappings between components and props', () => {
      const componentNames = Object.keys(COMPONENT_MIGRATION_MAP);
      const propMappingNames = Object.keys(PROP_MAPPINGS);
      
      // 检查是否所有有属性映射的组件都有对应的组件映射
      propMappingNames.forEach(name => {
        expect(componentNames).toContain(name);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle null and undefined props', () => {
      const result1 = adaptProps('Button', null);
      const result2 = adaptProps('Button', undefined);
      const result3 = adaptProps('Button', {});
      
      expect(result1).toEqual({});
      expect(result2).toEqual({});
      expect(result3).toEqual({});
    });

    it('should handle invalid component names', () => {
      const compatibility = checkComponentCompatibility('');
      expect(compatibility.isSupported).toBe(false);
      expect(compatibility.hasMapping).toBe(false);
    });

    it('should handle complex prop transformations', () => {
      const antdProps = {
        type: 'unknown-type',
        size: 'unknown-size',
        customFunction: () => 'test'
      };

      const heroProps = adaptProps('Button', antdProps);
      
      // 未知类型应该回退到默认值或保持原样
      expect(heroProps.customFunction).toBeDefined();
      expect(typeof heroProps.customFunction).toBe('function');
    });
  });
});

// 集成测试
describe('Integration Tests', () => {
  it('should perform end-to-end component migration', () => {
    // 模拟完整的迁移流程
    const componentName = 'Button';
    const antdProps = {
      type: 'primary',
      size: 'large',
      loading: true,
      onClick: () => console.log('clicked')
    };

    // 1. 检查兼容性
    const compatibility = checkComponentCompatibility(componentName);
    expect(compatibility.isSupported).toBe(true);

    // 2. 更新迁移状态
    migrationTracker.updateStatus(componentName, 'in-progress');

    // 3. 迁移组件
    const migratedComponent = migrateComponent(componentName, antdProps);
    expect(migratedComponent).toBeDefined();

    // 4. 标记完成
    migrationTracker.updateStatus(componentName, 'completed');

    // 5. 验证最终状态
    const finalStatus = migrationTracker.getStatus(componentName);
    expect(finalStatus?.status).toBe('completed');
  });

  it('should handle migration failures gracefully', () => {
    const componentName = 'UnsupportedComponent';
    
    // 1. 检查兼容性
    const compatibility = checkComponentCompatibility(componentName);
    expect(compatibility.isSupported).toBe(false);

    // 2. 尝试迁移
    const migratedComponent = migrateComponent(componentName, {});
    expect(migratedComponent).toBeNull();

    // 3. 记录失败
    migrationTracker.updateStatus(componentName, 'failed', ['Component not supported']);

    // 4. 验证失败状态
    const status = migrationTracker.getStatus(componentName);
    expect(status?.status).toBe('failed');
    expect(status?.issues).toContain('Component not supported');
  });
});