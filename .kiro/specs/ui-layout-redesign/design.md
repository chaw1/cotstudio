# Design Document

## Overview

This design document outlines the comprehensive UI/UX redesign for the COT Studio application. The redesign focuses on creating a modern, professional interface with a clean left navigation bar and main content area, inspired by contemporary data management platforms. The design addresses current layout issues, improves modal positioning, and enhances the overall visual appeal while maintaining functionality.

## Architecture

### Layout Structure
The application will use a two-column layout architecture:
- **Left Navigation Bar**: Fixed-width sidebar (240px expanded, 80px collapsed)
- **Main Content Area**: Flexible width area that adapts to remaining screen space
- **Modal Overlay System**: Centralized modal positioning that respects the navigation bar

### Component Hierarchy
```
MainLayout
├── Sidebar (Enhanced)
│   ├── Logo Section
│   ├── Main Navigation Menu
│   ├── Admin/Management Menu
│   └── User Controls Section (Bottom)
└── Content Area
    ├── Page Content
    └── Modal Container (Positioned correctly)
```

## Components and Interfaces

### 1. Enhanced Sidebar Component

**Location**: `frontend/src/components/layout/Sidebar.tsx`

**Key Improvements**:
- Reorganized navigation structure with clear visual hierarchy
- User controls moved to bottom section (login, settings, management)
- Improved visual design with modern color scheme
- Better responsive behavior

**Interface**:
```typescript
interface SidebarProps {
  collapsed: boolean;
  breakpoint?: string;
  isMobile?: boolean;
  onMobileClose?: () => void;
}
```

**Navigation Structure**:
- **Top Section**: Logo and branding
- **Main Menu**: Core functionality (Dashboard, Projects, CoT Annotation, Knowledge Graph, Export)
- **Admin Menu**: Management functions (User Management, System Settings)
- **Bottom Section**: User profile, notifications, logout

### 2. Modal Positioning System

**New Component**: `frontend/src/components/common/ModalContainer.tsx`

**Purpose**: Centralized modal management that ensures proper positioning relative to the sidebar

**Interface**:
```typescript
interface ModalContainerProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
  width?: number | string;
  centered?: boolean;
  children: React.ReactNode;
}
```

**Positioning Logic**:
- Calculate available content area width (screen width - sidebar width)
- Center modals within the content area, not the entire screen
- Ensure modals never overlap with the navigation bar
- Responsive positioning for mobile devices

### 3. Enhanced MainLayout Component

**Location**: `frontend/src/components/layout/MainLayout.tsx`

**Key Changes**:
- Remove header component (header-less design)
- Improve content area calculations
- Enhanced responsive behavior
- Better modal container integration

### 4. OCR Processing Modal Enhancement

**Location**: `frontend/src/components/ocr/OCRProcessingModal.tsx`

**Improvements**:
- Use new ModalContainer component
- Redesigned layout with better visual hierarchy
- Progress indicators and status displays
- Proper positioning within content area

## Data Models

### Theme Configuration
```typescript
interface AppTheme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    success: string;
    warning: string;
    error: string;
  };
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
  borderRadius: {
    sm: number;
    md: number;
    lg: number;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}
```

### Layout State Management
```typescript
interface LayoutState {
  sidebarCollapsed: boolean;
  sidebarWidth: number;
  contentAreaWidth: number;
  currentBreakpoint: string;
  isMobile: boolean;
  activeModals: string[];
}
```

## Visual Design System

### Color Palette
- **Primary**: #1677ff (Modern blue)
- **Secondary**: #52c41a (Success green)
- **Background**: #f5f5f5 (Light gray)
- **Surface**: #ffffff (White)
- **Navigation**: #001529 (Dark blue, similar to reference image)
- **Text Primary**: #262626 (Dark gray)
- **Text Secondary**: #8c8c8c (Medium gray)
- **Border**: #d9d9d9 (Light gray)

### Typography
- **Font Family**: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto
- **Base Size**: 14px
- **Headings**: 16px, 18px, 20px, 24px
- **Small Text**: 12px
- **Line Height**: 1.5 for body text, 1.2 for headings

### Spacing System
- **Base Unit**: 8px
- **Small**: 8px, 12px, 16px
- **Medium**: 20px, 24px, 32px
- **Large**: 40px, 48px, 64px

### Component Styling

#### Navigation Bar
- **Width**: 240px (expanded), 80px (collapsed)
- **Background**: #001529 (dark blue)
- **Text Color**: #ffffff
- **Hover Effects**: Subtle background color changes
- **Active State**: Highlighted with primary color accent

#### Main Content Area
- **Background**: #f5f5f5
- **Padding**: 24px (desktop), 16px (mobile)
- **Border Radius**: 8px for cards and containers
- **Shadow**: Subtle shadows for elevation

#### Modals
- **Background**: #ffffff
- **Border Radius**: 12px
- **Shadow**: Medium shadow for elevation
- **Backdrop**: Semi-transparent overlay with blur effect
- **Max Width**: 80% of content area
- **Positioning**: Centered within content area

## Error Handling

### Modal Positioning Errors
- Fallback to center of screen if content area calculation fails
- Minimum modal width constraints
- Responsive breakpoint handling

### Layout Calculation Errors
- Default sidebar width fallbacks
- Safe area calculations for mobile devices
- Graceful degradation for unsupported browsers

### Responsive Design Errors
- Breakpoint detection fallbacks
- Touch device detection
- Orientation change handling

## Testing Strategy

### Unit Tests
1. **Sidebar Component Tests**
   - Navigation menu rendering
   - Collapse/expand functionality
   - User controls interaction
   - Responsive behavior

2. **Modal Container Tests**
   - Positioning calculations
   - Responsive behavior
   - Overlay functionality
   - Accessibility compliance

3. **Layout Component Tests**
   - Content area calculations
   - Sidebar integration
   - Mobile responsiveness

### Integration Tests
1. **Navigation Flow Tests**
   - Route navigation from sidebar
   - Modal opening/closing
   - User authentication flow

2. **Responsive Layout Tests**
   - Breakpoint transitions
   - Mobile menu behavior
   - Content area adaptation

### Visual Regression Tests
1. **Layout Consistency**
   - Sidebar appearance across pages
   - Modal positioning accuracy
   - Content area alignment

2. **Theme Application**
   - Color scheme consistency
   - Typography rendering
   - Component styling

### Accessibility Tests
1. **Keyboard Navigation**
   - Tab order through sidebar
   - Modal focus management
   - Screen reader compatibility

2. **Color Contrast**
   - Text readability
   - Interactive element visibility
   - Focus indicators

## Implementation Approach

### Phase 1: Core Layout Structure
- Update MainLayout component
- Enhance Sidebar component
- Implement new color scheme and typography

### Phase 2: Modal System
- Create ModalContainer component
- Update existing modals to use new system
- Fix OCR processing modal positioning

### Phase 3: Visual Polish
- Apply new design system
- Enhance animations and transitions
- Optimize responsive behavior

### Phase 4: Testing and Refinement
- Comprehensive testing across devices
- Performance optimization
- Accessibility improvements

## Technical Considerations

### Performance
- CSS-in-JS optimization for theme switching
- Efficient re-rendering for layout changes
- Lazy loading for modal components

### Browser Compatibility
- Modern browser support (Chrome 90+, Firefox 88+, Safari 14+)
- Graceful degradation for older browsers
- CSS Grid and Flexbox fallbacks

### Mobile Optimization
- Touch-friendly interaction areas
- Optimized modal sizing for small screens
- Gesture support for sidebar toggle

### Accessibility
- WCAG 2.1 AA compliance
- Proper ARIA labels and roles
- Keyboard navigation support
- Screen reader optimization