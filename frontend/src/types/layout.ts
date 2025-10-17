// Layout types and interfaces
export interface ScreenSize {
  width: number;
  height: number;
}

export interface Breakpoint {
  name: string;
  minWidth: number;
  maxWidth?: number;
}

export interface LayoutDimensions {
  header: {
    height: number;
  };
  sidebar: {
    width: number;
    collapsedWidth: number;
  };
  footer: {
    height: number;
  };
  content: {
    padding: number;
    margin: number;
  };
}

export interface ResponsiveLayoutConfig {
  breakpoints: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
    xxl: number;
  };
  fixedAreas: {
    header: { height: number };
    sidebar: { width: number; collapsedWidth: number };
    footer: { height: number };
  };
  dynamicAreas: {
    workArea: { minWidth: number; flex: number };
    projectPanel: { minWidth: number; maxWidth: number };
    visualArea: { minWidth: number; flex: number };
  };
  contentSpacing: {
    padding: number;
    margin: number;
  };
}

export interface LayoutStyles {
  containerStyle: React.CSSProperties;
  headerStyle: React.CSSProperties;
  sidebarStyle: React.CSSProperties;
  bodyStyle: React.CSSProperties;
  workAreaStyle: React.CSSProperties;
  footerStyle: React.CSSProperties;
}

export interface ResponsiveLayoutState {
  screenSize: ScreenSize;
  currentBreakpoint: string;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  layoutConfig: ResponsiveLayoutConfig;
  layoutStyles: LayoutStyles;
  sidebarCollapsed: boolean;
}

export type LayoutDebugInfo = {
  screenSize: ScreenSize;
  breakpoint: string;
  layoutDimensions: LayoutDimensions;
  calculatedStyles: LayoutStyles;
  performance?: {
    renderTime: number;
    actualDimensions: {
      width: number;
      height: number;
    };
    contentArea: {
      width: number;
      height: number;
    };
    memoryUsage?: {
      used: number;
      total: number;
      limit: number;
    } | null;
  };
  accessibility?: {
    reducedMotion: boolean;
    highContrast: boolean;
    colorScheme: 'light' | 'dark';
  };
};