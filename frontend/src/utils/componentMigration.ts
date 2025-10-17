import React from 'react';
import {
  Button as HeroButton,
  Card as HeroCard,
  Table as HeroTable,
  Input as HeroInput,
  Select as HeroSelect,
  Modal as HeroModal,
  Tabs as HeroTabs,
  Chip as HeroChip,
  Avatar as HeroAvatar,
  Divider as HeroDivider,
  Spinner as HeroSpinner,
  Switch as HeroSwitch,
  Checkbox as HeroCheckbox,
  Radio as HeroRadio,
  Slider as HeroSlider,
  Progress as HeroProgress,
  Badge as HeroBadge,
  Tooltip as HeroTooltip,
  Popover as HeroPopover,
  Dropdown as HeroDropdown,
  Breadcrumbs as HeroBreadcrumbs,
  Pagination as HeroPagination,
  Link as HeroLink,
  Image as HeroImage,
  Code as HeroCode,
  Snippet as HeroSnippet,
  Kbd as HeroKbd,
  Spacer as HeroSpacer,
  User as HeroUser,
  Listbox as HeroListbox,
  ScrollShadow as HeroScrollShadow,
  Accordion as HeroAccordion,
  DatePicker as HeroDatePicker,
  TimeInput as HeroTimeInput,
  Autocomplete as HeroAutocomplete,
  CheckboxGroup as HeroCheckboxGroup,
  RadioGroup as HeroRadioGroup,
  ButtonGroup as HeroButtonGroup,
  CardBody,
  CardHeader,
  CardFooter,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Tab,
  SelectItem,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
  BreadcrumbItem,
  ListboxItem,
  AccordionItem,
  CheckboxGroupProps,
  RadioGroupProps,
  ButtonProps as HeroButtonProps,
  CardProps as HeroCardProps,
  InputProps as HeroInputProps,
  SelectProps as HeroSelectProps,
  ModalProps as HeroModalProps,
  TableProps as HeroTableProps,
  TabsProps as HeroTabsProps,
} from '@heroui/react';

// Ant Design 到 HeroUI 的组件映射
export const COMPONENT_MIGRATION_MAP = {
  // 基础组件
  'Button': HeroButton,
  'Card': HeroCard,
  'Input': HeroInput,
  'Select': HeroSelect,
  'Modal': HeroModal,
  'Table': HeroTable,
  'Tabs': HeroTabs,
  'Tag': HeroChip,
  'Avatar': HeroAvatar,
  'Divider': HeroDivider,
  'Spin': HeroSpinner,
  'Switch': HeroSwitch,
  'Checkbox': HeroCheckbox,
  'Radio': HeroRadio,
  'Slider': HeroSlider,
  'Progress': HeroProgress,
  'Badge': HeroBadge,
  'Tooltip': HeroTooltip,
  'Popover': HeroPopover,
  'Dropdown': HeroDropdown,
  'Breadcrumb': HeroBreadcrumbs,
  'Pagination': HeroPagination,
  'Typography.Link': HeroLink,
  'Image': HeroImage,
  'Code': HeroCode,
  'Space': HeroSpacer,
  'List': HeroListbox,
  'Collapse': HeroAccordion,
  'DatePicker': HeroDatePicker,
  'TimePicker': HeroTimeInput,
  'AutoComplete': HeroAutocomplete,
};

// 属性映射配置
interface PropMapping {
  [antdProp: string]: string | ((value: any) => any) | null;
}

// Ant Design 到 HeroUI 的属性映射
export const PROP_MAPPINGS: { [component: string]: PropMapping } = {
  Button: {
    type: (value: string) => {
      const typeMap: { [key: string]: string } = {
        'default': 'default',
        'primary': 'primary',
        'dashed': 'bordered',
        'text': 'light',
        'link': 'light'
      };
      return typeMap[value] || 'default';
    },
    size: (value: string) => {
      const sizeMap: { [key: string]: string } = {
        'small': 'sm',
        'middle': 'md',
        'large': 'lg'
      };
      return sizeMap[value] || 'md';
    },
    loading: 'isLoading',
    disabled: 'isDisabled',
    danger: (value: boolean) => value ? { color: 'danger' } : undefined,
    ghost: (value: boolean) => value ? { variant: 'ghost' } : undefined,
    block: (value: boolean) => value ? { fullWidth: true } : undefined,
  },
  
  Card: {
    title: 'title',
    extra: 'extra',
    bordered: (value: boolean) => !value ? { shadow: 'none' } : undefined,
    hoverable: (value: boolean) => value ? { isPressable: true } : undefined,
    loading: 'isLoading',
    size: (value: string) => {
      const sizeMap: { [key: string]: string } = {
        'small': 'sm',
        'default': 'md',
        'large': 'lg'
      };
      return sizeMap[value] || 'md';
    },
  },
  
  Input: {
    placeholder: 'placeholder',
    disabled: 'isDisabled',
    size: (value: string) => {
      const sizeMap: { [key: string]: string } = {
        'small': 'sm',
        'middle': 'md',
        'large': 'lg'
      };
      return sizeMap[value] || 'md';
    },
    prefix: 'startContent',
    suffix: 'endContent',
    addonBefore: 'startContent',
    addonAfter: 'endContent',
    allowClear: 'isClearable',
    bordered: (value: boolean) => !value ? { variant: 'underlined' } : undefined,
  },
  
  Select: {
    placeholder: 'placeholder',
    disabled: 'isDisabled',
    size: (value: string) => {
      const sizeMap: { [key: string]: string } = {
        'small': 'sm',
        'middle': 'md',
        'large': 'lg'
      };
      return sizeMap[value] || 'md';
    },
    allowClear: 'isClearable',
    mode: (value: string) => {
      return value === 'multiple' ? { selectionMode: 'multiple' } : undefined;
    },
    showSearch: (value: boolean) => value ? { isSearchable: true } : undefined,
    loading: 'isLoading',
    bordered: (value: boolean) => !value ? { variant: 'underlined' } : undefined,
  },
  
  Modal: {
    visible: 'isOpen',
    title: 'title',
    width: 'size',
    centered: (value: boolean) => value ? { placement: 'center' } : undefined,
    closable: (value: boolean) => !value ? { hideCloseButton: true } : undefined,
    maskClosable: (value: boolean) => !value ? { isDismissable: false } : undefined,
    confirmLoading: 'isLoading',
    destroyOnClose: (value: boolean) => value ? { shouldBlockScroll: false } : undefined,
  },
  
  Table: {
    dataSource: 'data',
    columns: 'columns',
    loading: 'isLoading',
    pagination: 'pagination',
    size: (value: string) => {
      const sizeMap: { [key: string]: string } = {
        'small': 'sm',
        'middle': 'md',
        'large': 'lg'
      };
      return sizeMap[value] || 'md';
    },
    bordered: (value: boolean) => value ? { showBorder: true } : undefined,
    scroll: (value: any) => value ? { isVirtualized: true } : undefined,
  },
  
  Tabs: {
    activeKey: 'selectedKey',
    defaultActiveKey: 'defaultSelectedKey',
    type: (value: string) => {
      const typeMap: { [key: string]: string } = {
        'line': 'underlined',
        'card': 'bordered',
        'editable-card': 'bordered'
      };
      return typeMap[value] || 'underlined';
    },
    size: (value: string) => {
      const sizeMap: { [key: string]: string } = {
        'small': 'sm',
        'middle': 'md',
        'large': 'lg'
      };
      return sizeMap[value] || 'md';
    },
    tabPosition: 'placement',
    centered: (value: boolean) => value ? { justify: 'center' } : undefined,
  },
};

// 属性适配函数
export const adaptProps = (componentName: string, antdProps: any): any => {
  // 处理 null 和 undefined 的情况
  if (!antdProps || typeof antdProps !== 'object') {
    return {};
  }
  
  const mapping = PROP_MAPPINGS[componentName];
  if (!mapping) return antdProps;
  
  const heroProps: any = {};
  const unmappedProps: any = {};
  
  Object.keys(antdProps).forEach(prop => {
    const mappedProp = mapping[prop];
    
    if (mappedProp === null) {
      // 忽略此属性
      return;
    } else if (typeof mappedProp === 'string') {
      // 直接映射属性名
      heroProps[mappedProp] = antdProps[prop];
    } else if (typeof mappedProp === 'function') {
      // 使用函数转换属性值
      const result = mappedProp(antdProps[prop]);
      if (result !== undefined) {
        if (typeof result === 'object') {
          Object.assign(heroProps, result);
        } else {
          heroProps[prop] = result;
        }
      }
    } else {
      // 未映射的属性保持原样
      unmappedProps[prop] = antdProps[prop];
    }
  });
  
  return { ...heroProps, ...unmappedProps };
};

// 组件迁移工具函数
export const migrateComponent = (
  componentName: string, 
  props: any, 
  children?: React.ReactNode
): React.ReactElement | null => {
  const HeroComponent = COMPONENT_MIGRATION_MAP[componentName as keyof typeof COMPONENT_MIGRATION_MAP];
  
  if (!HeroComponent) {
    console.warn(`Component ${componentName} not found in migration map`);
    return null;
  }
  
  const adaptedProps = adaptProps(componentName, props);
  
  return React.createElement(HeroComponent, adaptedProps, children);
};

// 批量组件迁移工具
export const createMigratedComponent = <T extends Record<string, any>>(
  componentName: string,
  defaultProps?: Partial<T>
) => {
  return React.forwardRef<any, T>((props, ref) => {
    const mergedProps = { ...defaultProps, ...props, ref };
    return migrateComponent(componentName, mergedProps, props.children);
  });
};

// 兼容性检查工具
export const checkComponentCompatibility = (componentName: string): {
  isSupported: boolean;
  hasMapping: boolean;
  missingFeatures: string[];
} => {
  const isSupported = componentName in COMPONENT_MIGRATION_MAP;
  const hasMapping = componentName in PROP_MAPPINGS;
  
  // 检查可能缺失的功能
  const missingFeatures: string[] = [];
  
  // 根据组件类型检查特定功能
  switch (componentName) {
    case 'Table':
      // HeroUI Table 可能缺少的 Ant Design 功能
      missingFeatures.push('expandable rows', 'column grouping', 'tree data');
      break;
    case 'Form':
      // HeroUI 没有直接的 Form 组件
      missingFeatures.push('form validation', 'form layout', 'form items');
      break;
    case 'DatePicker':
      // 检查日期选择器功能
      missingFeatures.push('range picker', 'time picker integration');
      break;
    case 'Upload':
      // HeroUI 可能没有上传组件
      missingFeatures.push('file upload', 'drag and drop', 'progress tracking');
      break;
  }
  
  return {
    isSupported,
    hasMapping,
    missingFeatures
  };
};

// 迁移状态跟踪
export interface MigrationStatus {
  componentName: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  issues: string[];
  lastUpdated: Date;
}

export class MigrationTracker {
  private static instance: MigrationTracker;
  private migrations: Map<string, MigrationStatus> = new Map();
  
  static getInstance(): MigrationTracker {
    if (!MigrationTracker.instance) {
      MigrationTracker.instance = new MigrationTracker();
    }
    return MigrationTracker.instance;
  }
  
  updateStatus(componentName: string, status: MigrationStatus['status'], issues: string[] = []): void {
    this.migrations.set(componentName, {
      componentName,
      status,
      issues,
      lastUpdated: new Date()
    });
  }
  
  getStatus(componentName: string): MigrationStatus | undefined {
    return this.migrations.get(componentName);
  }
  
  getAllStatuses(): MigrationStatus[] {
    return Array.from(this.migrations.values());
  }
  
  getProgress(): { completed: number; total: number; percentage: number } {
    const statuses = this.getAllStatuses();
    const completed = statuses.filter(s => s.status === 'completed').length;
    const total = statuses.length;
    const percentage = total > 0 ? (completed / total) * 100 : 0;
    
    return { completed, total, percentage };
  }
}

// 导出迁移跟踪器实例
export const migrationTracker = MigrationTracker.getInstance();

// 开发工具：组件使用情况分析
export const analyzeComponentUsage = (codebase: string): {
  antdComponents: string[];
  migrationCandidates: string[];
  complexComponents: string[];
} => {
  const antdImportRegex = /import\s+{([^}]+)}\s+from\s+['"]antd['"]/g;
  const antdComponents: Set<string> = new Set();
  
  let match;
  while ((match = antdImportRegex.exec(codebase)) !== null) {
    const components = match[1].split(',').map(c => c.trim());
    components.forEach(comp => antdComponents.add(comp));
  }
  
  const allComponents = Array.from(antdComponents);
  const migrationCandidates = allComponents.filter(comp => 
    comp in COMPONENT_MIGRATION_MAP
  );
  const complexComponents = allComponents.filter(comp => {
    const compatibility = checkComponentCompatibility(comp);
    return compatibility.missingFeatures.length > 0;
  });
  
  return {
    antdComponents: allComponents,
    migrationCandidates,
    complexComponents
  };
};

export default {
  COMPONENT_MIGRATION_MAP,
  PROP_MAPPINGS,
  adaptProps,
  migrateComponent,
  createMigratedComponent,
  checkComponentCompatibility,
  migrationTracker,
  analyzeComponentUsage
};