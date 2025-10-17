import React, { useEffect, useCallback, useMemo, useRef } from 'react';
import { Modal, ModalProps } from 'antd';
import { useResponsiveLayout } from '../../hooks/useResponsiveLayout';
import { useAccessibility, ScreenReaderOnly } from '../../hooks/useAccessibility';
import '../../styles/accessibility.css';

interface ModalContainerProps extends Omit<ModalProps, 'getContainer'> {
  visible: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  width?: number | string;
  centered?: boolean;
  children: React.ReactNode;
  zIndex?: number;
  destroyOnClose?: boolean;
  footer?: React.ReactNode;
}

/**
 * ModalContainer - 智能模态框容器组件
 * 
 * 功能特性：
 * - 响应式宽度调整
 * - 无障碍支持
 * - 焦点管理
 * - 键盘导航
 */
const ModalContainer: React.FC<ModalContainerProps> = ({
  visible,
  onClose,
  title,
  width = 520,
  centered = true,
  children,
  zIndex = 1050,
  destroyOnClose = true,
  footer,
  ...modalProps
}) => {
  const {
    isMobile,
    isTablet,
    screenSize
  } = useResponsiveLayout();

  const { useFocusTrap, useKeyboardNavigation, announceToScreenReader, generateId } = useAccessibility();
  const modalRef = useFocusTrap(visible);
  const titleId = generateId('modal-title');
  const descriptionId = generateId('modal-description');

  // 计算模态框的响应式宽度
  const responsiveWidth = useMemo(() => {
    if (typeof width === 'string') return width;
    
    // 响应式宽度调整
    if (isMobile) {
      return Math.min(width, screenSize.width - 32); // 移动端留16px边距
    } else if (isTablet) {
      return Math.min(width, screenSize.width * 0.8); // 平板80%宽度
    }
    
    return width;
  }, [width, isMobile, isTablet, screenSize.width]);

  // 键盘导航和焦点管理
  useKeyboardNavigation(
    // Escape key - close modal
    () => {
      if (visible) {
        announceToScreenReader('模态框已关闭');
        onClose();
      }
    }
  );

  // 模态框打开时的无障碍处理
  useEffect(() => {
    if (visible) {
      // 通知屏幕阅读器模态框已打开
      announceToScreenReader(`模态框已打开${title ? `：${title}` : ''}`, 'assertive');
      
      // 设置页面其他内容为不可访问
      const mainContent = document.getElementById('main-content');
      const sidebar = document.querySelector('.sidebar-navigation');
      
      if (mainContent) {
        mainContent.setAttribute('aria-hidden', 'true');
        mainContent.setAttribute('inert', '');
      }
      if (sidebar) {
        sidebar.setAttribute('aria-hidden', 'true');
        sidebar.setAttribute('inert', '');
      }

      return () => {
        // 恢复页面其他内容的可访问性
        if (mainContent) {
          mainContent.removeAttribute('aria-hidden');
          mainContent.removeAttribute('inert');
        }
        if (sidebar) {
          sidebar.removeAttribute('aria-hidden');
          sidebar.removeAttribute('inert');
        }
      };
    }
  }, [visible, title, announceToScreenReader]);

  if (!visible) {
    return null;
  }

  return (
    <div ref={modalRef}>
      <Modal
        {...modalProps}
        open={visible}
        onCancel={onClose}
        title={title}
        width={responsiveWidth}
        centered={centered}
        destroyOnClose={destroyOnClose}
        mask={true}
        maskClosable={true}
        zIndex={zIndex}
        footer={footer}
        style={{
          ...modalProps.style
        }}
        wrapClassName={`modal-container-wrap ${modalProps.wrapClassName || ''}`}
        modalRender={(modal) => (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby={title ? titleId : undefined}
            aria-describedby={descriptionId}
            tabIndex={-1}
          >
            {modal}
          </div>
        )}
      >
        {/* Hidden title for screen readers if title is provided - only if no visible title */}
        {title && !modalProps.title && (
          <ScreenReaderOnly>
            <h2 id={titleId}>{title}</h2>
          </ScreenReaderOnly>
        )}
        
        {/* Content wrapper with description ID */}
        <div id={descriptionId}>
          {children}
        </div>
      </Modal>
    </div>
  );
};

export default ModalContainer;