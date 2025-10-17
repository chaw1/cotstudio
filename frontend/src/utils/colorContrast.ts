/**
 * Color Contrast Utilities
 * 
 * 用于验证颜色对比度是否符合 WCAG 2.1 AA 标准
 */

// WCAG 2.1 对比度标准
export const WCAG_STANDARDS = {
  AA_NORMAL: 4.5,      // 普通文本 AA 级别
  AA_LARGE: 3,         // 大文本 AA 级别
  AAA_NORMAL: 7,       // 普通文本 AAA 级别
  AAA_LARGE: 4.5,      // 大文本 AAA 级别
} as const;

/**
 * 将十六进制颜色转换为 RGB
 */
export function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

/**
 * 计算相对亮度
 * 基于 WCAG 2.1 规范
 */
export function getRelativeLuminance(r: number, g: number, b: number): number {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

/**
 * 计算两个颜色之间的对比度
 */
export function getContrastRatio(color1: string, color2: string): number {
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);
  
  if (!rgb1 || !rgb2) {
    throw new Error('Invalid color format. Please use hex format (#RRGGBB)');
  }
  
  const l1 = getRelativeLuminance(rgb1.r, rgb1.g, rgb1.b);
  const l2 = getRelativeLuminance(rgb2.r, rgb2.g, rgb2.b);
  
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * 检查颜色对比度是否符合 WCAG 标准
 */
export function checkContrastCompliance(
  foreground: string,
  background: string,
  isLargeText: boolean = false,
  level: 'AA' | 'AAA' = 'AA'
): {
  ratio: number;
  compliant: boolean;
  standard: number;
  level: string;
} {
  const ratio = getContrastRatio(foreground, background);
  
  let standard: number;
  if (level === 'AAA') {
    standard = isLargeText ? WCAG_STANDARDS.AAA_LARGE : WCAG_STANDARDS.AAA_NORMAL;
  } else {
    standard = isLargeText ? WCAG_STANDARDS.AA_LARGE : WCAG_STANDARDS.AA_NORMAL;
  }
  
  return {
    ratio: Math.round(ratio * 100) / 100,
    compliant: ratio >= standard,
    standard,
    level: `${level} ${isLargeText ? 'Large' : 'Normal'}`
  };
}

/**
 * 获取建议的文本颜色（黑色或白色）
 */
export function getRecommendedTextColor(backgroundColor: string): '#000000' | '#ffffff' {
  const whiteContrast = getContrastRatio('#ffffff', backgroundColor);
  const blackContrast = getContrastRatio('#000000', backgroundColor);
  
  return whiteContrast > blackContrast ? '#ffffff' : '#000000';
}

/**
 * 验证设计系统中的颜色对比度
 */
export function validateDesignSystemColors(): {
  results: Array<{
    combination: string;
    foreground: string;
    background: string;
    ratio: number;
    compliant: boolean;
    recommendation?: string;
  }>;
  summary: {
    total: number;
    compliant: number;
    nonCompliant: number;
  };
} {
  // 设计系统中的主要颜色组合
  const colorCombinations = [
    // 主要文本颜色
    { name: 'Primary Text on White', fg: '#262626', bg: '#ffffff' },
    { name: 'Secondary Text on White', fg: '#8c8c8c', bg: '#ffffff' },
    { name: 'Tertiary Text on White', fg: '#bfbfbf', bg: '#ffffff' },
    
    // 按钮颜色
    { name: 'Primary Button Text', fg: '#ffffff', bg: '#1677ff' },
    { name: 'Success Button Text', fg: '#ffffff', bg: '#52c41a' },
    { name: 'Warning Button Text', fg: '#ffffff', bg: '#faad14' },
    { name: 'Error Button Text', fg: '#ffffff', bg: '#ff4d4f' },
    
    // 侧边栏颜色
    { name: 'Sidebar Text', fg: '#ffffff', bg: '#001529' },
    { name: 'Sidebar Secondary Text', fg: 'rgba(255, 255, 255, 0.85)', bg: '#001529' },
    
    // 状态颜色
    { name: 'Success Text', fg: '#389e0d', bg: '#ffffff' },
    { name: 'Warning Text', fg: '#d48806', bg: '#ffffff' },
    { name: 'Error Text', fg: '#cf1322', bg: '#ffffff' },
    { name: 'Info Text', fg: '#0958d9', bg: '#ffffff' },
    
    // 卡片和容器
    { name: 'Text on Card Background', fg: '#262626', bg: '#fafafa' },
    { name: 'Text on Layout Background', fg: '#262626', bg: '#f5f5f5' },
  ];
  
  const results = colorCombinations.map(combo => {
    // 处理 rgba 颜色
    let fg = combo.fg;
    let bg = combo.bg;
    
    // 简化处理：将 rgba 转换为近似的 hex 值
    if (fg.includes('rgba')) {
      fg = '#d9d9d9'; // 近似值
    }
    if (bg.includes('rgba')) {
      bg = '#001529'; // 近似值
    }
    
    try {
      const compliance = checkContrastCompliance(fg, bg);
      
      let recommendation = '';
      if (!compliance.compliant) {
        const recommendedColor = getRecommendedTextColor(bg);
        recommendation = `建议使用 ${recommendedColor} 作为文本颜色`;
      }
      
      return {
        combination: combo.name,
        foreground: fg,
        background: bg,
        ratio: compliance.ratio,
        compliant: compliance.compliant,
        recommendation
      };
    } catch (error) {
      return {
        combination: combo.name,
        foreground: fg,
        background: bg,
        ratio: 0,
        compliant: false,
        recommendation: '颜色格式错误，无法计算对比度'
      };
    }
  });
  
  const compliant = results.filter(r => r.compliant).length;
  
  return {
    results,
    summary: {
      total: results.length,
      compliant,
      nonCompliant: results.length - compliant
    }
  };
}

/**
 * 生成对比度报告
 */
export function generateContrastReport(): string {
  const validation = validateDesignSystemColors();
  
  let report = '# 颜色对比度验证报告\n\n';
  report += `## 总结\n`;
  report += `- 总计颜色组合: ${validation.summary.total}\n`;
  report += `- 符合标准: ${validation.summary.compliant}\n`;
  report += `- 不符合标准: ${validation.summary.nonCompliant}\n`;
  report += `- 合规率: ${Math.round((validation.summary.compliant / validation.summary.total) * 100)}%\n\n`;
  
  report += `## 详细结果\n\n`;
  
  validation.results.forEach(result => {
    const status = result.compliant ? '✅ 通过' : '❌ 不通过';
    report += `### ${result.combination}\n`;
    report += `- 前景色: ${result.foreground}\n`;
    report += `- 背景色: ${result.background}\n`;
    report += `- 对比度: ${result.ratio}:1\n`;
    report += `- 状态: ${status}\n`;
    if (result.recommendation) {
      report += `- 建议: ${result.recommendation}\n`;
    }
    report += '\n';
  });
  
  return report;
}

/**
 * 在开发环境中输出对比度报告
 */
export function logContrastReport(): void {
  if (process.env.NODE_ENV === 'development') {
    console.group('🎨 颜色对比度验证报告');
    
    const validation = validateDesignSystemColors();
    
    console.log(`总计: ${validation.summary.total} 个颜色组合`);
    console.log(`✅ 符合标准: ${validation.summary.compliant}`);
    console.log(`❌ 不符合标准: ${validation.summary.nonCompliant}`);
    console.log(`📊 合规率: ${Math.round((validation.summary.compliant / validation.summary.total) * 100)}%`);
    
    if (validation.summary.nonCompliant > 0) {
      console.warn('以下颜色组合不符合 WCAG 2.1 AA 标准:');
      validation.results
        .filter(r => !r.compliant)
        .forEach(result => {
          console.warn(`- ${result.combination}: ${result.ratio}:1 (需要 ≥4.5:1)`);
          if (result.recommendation) {
            console.info(`  建议: ${result.recommendation}`);
          }
        });
    }
    
    console.groupEnd();
  }
}