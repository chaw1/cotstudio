// HeroUI theme configuration without createTheme (using direct theme object)

// HeroUI主题配置
export const heroUITheme = {
  type: 'light',
  theme: {
    colors: {
      // 主色调 - 与现有Ant Design主题保持一致
      primary: {
        50: '#e6f4ff',
        100: '#bae0ff',
        200: '#91caff',
        300: '#69b1ff',
        400: '#4096ff',
        500: '#1677ff',
        600: '#0958d9',
        700: '#003eb3',
        800: '#002c8c',
        900: '#001d66',
        DEFAULT: '#1677ff',
        foreground: '#ffffff'
      },
      secondary: {
        50: '#f6ffed',
        100: '#d9f7be',
        200: '#b7eb8f',
        300: '#95de64',
        400: '#73d13d',
        500: '#52c41a',
        600: '#389e0d',
        700: '#237804',
        800: '#135200',
        900: '#092b00',
        DEFAULT: '#52c41a',
        foreground: '#ffffff'
      },
      success: {
        50: '#f6ffed',
        100: '#d9f7be',
        200: '#b7eb8f',
        300: '#95de64',
        400: '#73d13d',
        500: '#52c41a',
        600: '#389e0d',
        700: '#237804',
        800: '#135200',
        900: '#092b00',
        DEFAULT: '#52c41a',
        foreground: '#ffffff'
      },
      warning: {
        50: '#fffbe6',
        100: '#fff1b8',
        200: '#ffe58f',
        300: '#ffd666',
        400: '#ffc53d',
        500: '#faad14',
        600: '#d48806',
        700: '#ad6800',
        800: '#874d00',
        900: '#613400',
        DEFAULT: '#faad14',
        foreground: '#ffffff'
      },
      danger: {
        50: '#fff2f0',
        100: '#ffccc7',
        200: '#ffa39e',
        300: '#ff7875',
        400: '#ff4d4f',
        500: '#f5222d',
        600: '#cf1322',
        700: '#a8071a',
        800: '#820014',
        900: '#5c0011',
        DEFAULT: '#ff4d4f',
        foreground: '#ffffff'
      },
      // 背景色
      background: '#ffffff',
      foreground: '#262626',
      // 内容背景
      content1: '#ffffff',
      content2: '#fafafa',
      content3: '#f5f5f5',
      content4: '#f0f0f0',
      // 默认颜色
      default: {
        50: '#fafafa',
        100: '#f5f5f5',
        200: '#f0f0f0',
        300: '#d9d9d9',
        400: '#bfbfbf',
        500: '#8c8c8c',
        600: '#595959',
        700: '#434343',
        800: '#262626',
        900: '#1f1f1f',
        DEFAULT: '#d9d9d9',
        foreground: '#262626'
      }
    },
    layout: {
      // 圆角设置
      radius: {
        small: '6px',
        medium: '8px',
        large: '12px'
      },
      // 边框宽度
      borderWidth: {
        small: '1px',
        medium: '2px',
        large: '3px'
      },
      // 禁用状态透明度
      disabledOpacity: 0.5,
      // 分割线透明度
      dividerWeight: '1px',
      // 字体大小
      fontSize: {
        tiny: '0.75rem',    // 12px
        small: '0.875rem',  // 14px
        medium: '1rem',     // 16px
        large: '1.125rem',  // 18px
      },
      // 行高
      lineHeight: {
        tiny: '1rem',
        small: '1.25rem',
        medium: '1.5rem',
        large: '1.75rem',
      }
    },
    spacing: {
      // 间距设置 - 与Ant Design保持一致
      unit: 4, // 基础单位 4px
      xs: '0.5rem',   // 8px
      sm: '0.75rem',  // 12px
      md: '1rem',     // 16px
      lg: '1.5rem',   // 24px
      xl: '2rem',     // 32px
      '2xl': '2.5rem', // 40px
      '3xl': '3rem',   // 48px
    }
  }
};

// 暗色主题配置（可选）
export const heroUIDarkTheme = {
  type: 'dark',
  theme: {
    colors: {
      primary: {
        50: '#001d66',
        100: '#002c8c',
        200: '#003eb3',
        300: '#0958d9',
        400: '#1677ff',
        500: '#4096ff',
        600: '#69b1ff',
        700: '#91caff',
        800: '#bae0ff',
        900: '#e6f4ff',
        DEFAULT: '#1677ff',
        foreground: '#ffffff'
      },
      background: '#141414',
      foreground: '#ffffff',
      content1: '#1f1f1f',
      content2: '#262626',
      content3: '#434343',
      content4: '#595959',
    }
  }
};

// 主题配置导出
export const themeConfig = {
  light: heroUITheme,
  dark: heroUIDarkTheme
};

export default heroUITheme;