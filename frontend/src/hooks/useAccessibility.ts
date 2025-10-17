import React, { useEffect, useRef, useCallback } from 'react';

/**
 * Accessibility utilities hook
 * Provides common accessibility functions and keyboard navigation support
 */
export const useAccessibility = () => {
  /**
   * Focus trap for modal dialogs
   */
  const useFocusTrap = (isActive: boolean) => {
    const containerRef = useRef<HTMLElement>(null);
    const previousActiveElement = useRef<Element | null>(null);

    useEffect(() => {
      if (!isActive || !containerRef.current) return;

      // Store the previously focused element
      previousActiveElement.current = document.activeElement;

      const container = containerRef.current;
      const focusableElements = container.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      // Focus the first element
      if (firstElement) {
        firstElement.focus();
      }

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key !== 'Tab') return;

        if (e.shiftKey) {
          // Shift + Tab
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          }
        } else {
          // Tab
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      };

      container.addEventListener('keydown', handleKeyDown);

      return () => {
        container.removeEventListener('keydown', handleKeyDown);
        
        // Restore focus to the previously active element
        if (previousActiveElement.current instanceof HTMLElement) {
          previousActiveElement.current.focus();
        }
      };
    }, [isActive]);

    return containerRef;
  };

  /**
   * Keyboard navigation handler
   */
  const useKeyboardNavigation = (
    onEscape?: () => void,
    onEnter?: () => void,
    onArrowKeys?: (direction: 'up' | 'down' | 'left' | 'right') => void
  ) => {
    const handleKeyDown = useCallback((e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          onEscape?.();
          break;
        case 'Enter':
          onEnter?.();
          break;
        case 'ArrowUp':
          e.preventDefault();
          onArrowKeys?.('up');
          break;
        case 'ArrowDown':
          e.preventDefault();
          onArrowKeys?.('down');
          break;
        case 'ArrowLeft':
          e.preventDefault();
          onArrowKeys?.('left');
          break;
        case 'ArrowRight':
          e.preventDefault();
          onArrowKeys?.('right');
          break;
      }
    }, [onEscape, onEnter, onArrowKeys]);

    useEffect(() => {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }, [handleKeyDown]);
  };

  /**
   * Announce to screen readers
   */
  const announceToScreenReader = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }, []);

  /**
   * Skip link functionality
   */
  const createSkipLink = useCallback((targetId: string, label: string) => {
    const skipLink = document.createElement('a');
    skipLink.href = `#${targetId}`;
    skipLink.textContent = label;
    skipLink.className = 'skip-link';
    skipLink.style.cssText = `
      position: absolute;
      top: -40px;
      left: 6px;
      background: #000;
      color: #fff;
      padding: 8px;
      text-decoration: none;
      border-radius: 4px;
      z-index: 9999;
      transition: top 0.3s;
    `;
    
    skipLink.addEventListener('focus', () => {
      skipLink.style.top = '6px';
    });
    
    skipLink.addEventListener('blur', () => {
      skipLink.style.top = '-40px';
    });
    
    return skipLink;
  }, []);

  /**
   * Generate unique IDs for ARIA relationships
   */
  const generateId = useCallback((prefix: string = 'a11y') => {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  return {
    useFocusTrap,
    useKeyboardNavigation,
    announceToScreenReader,
    createSkipLink,
    generateId
  };
};

/**
 * Screen reader only text utility
 */
export const ScreenReaderOnly = ({ children }: { children: React.ReactNode }) => {
  return React.createElement('span', { className: 'sr-only' }, children);
};

/**
 * Focus management utilities
 */
export const focusUtils = {
  /**
   * Move focus to element by ID
   */
  focusElement: (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.focus();
    }
  },

  /**
   * Focus first focusable element in container
   */
  focusFirstInContainer: (container: HTMLElement) => {
    const focusable = container.querySelector(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as HTMLElement;
    
    if (focusable) {
      focusable.focus();
    }
  },

  /**
   * Check if element is focusable
   */
  isFocusable: (element: HTMLElement): boolean => {
    const focusableSelectors = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    return element.matches(focusableSelectors) && !element.hasAttribute('disabled');
  }
};