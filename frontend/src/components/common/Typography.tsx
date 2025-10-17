import React from 'react';
import { Typography as AntTypography } from 'antd';

const { Title: AntTitle, Text: AntText, Paragraph: AntParagraph } = AntTypography;

// Enhanced Title Component
interface EnhancedTitleProps {
  variant?: 'display' | 'heading' | 'subheading';
  gradient?: boolean;
  weight?: 'light' | 'normal' | 'medium' | 'semibold' | 'bold';
  level?: 1 | 2 | 3 | 4 | 5;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

export const Title: React.FC<EnhancedTitleProps> = ({
  variant = 'heading',
  gradient = false,
  weight = 'semibold',
  className = '',
  style = {},
  children,
  ...props
}) => {
  const getLevel = (): 1 | 2 | 3 | 4 | 5 => {
    switch (variant) {
      case 'display':
        return 1;
      case 'heading':
        return 2;
      case 'subheading':
        return 3;
      default:
        return 2;
    }
  };

  const getStyle = (): React.CSSProperties => {
    const baseStyle: React.CSSProperties = {
      fontWeight: getFontWeight(),
      lineHeight: getLineHeight(),
      letterSpacing: getLetterSpacing(),
      ...style,
    };

    if (gradient) {
      return {
        ...baseStyle,
        background: 'linear-gradient(135deg, #1677ff 0%, #4096ff 100%)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
      };
    }

    return baseStyle;
  };

  const getFontWeight = () => {
    switch (weight) {
      case 'light':
        return 300;
      case 'normal':
        return 400;
      case 'medium':
        return 500;
      case 'semibold':
        return 600;
      case 'bold':
        return 700;
      default:
        return 600;
    }
  };

  const getLineHeight = () => {
    switch (variant) {
      case 'display':
        return 1.1;
      case 'heading':
        return 1.2;
      case 'subheading':
        return 1.3;
      default:
        return 1.2;
    }
  };

  const getLetterSpacing = () => {
    switch (variant) {
      case 'display':
        return '-0.02em';
      case 'heading':
        return '-0.01em';
      default:
        return 'normal';
    }
  };

  return (
    <AntTitle
      level={level || getLevel()}
      className={`enhanced-title ${className}`}
      style={getStyle()}
    >
      {children}
    </AntTitle>
  );
};

// Enhanced Text Component
interface EnhancedTextProps {
  variant?: 'body' | 'caption' | 'overline' | 'label';
  weight?: 'light' | 'normal' | 'medium' | 'semibold' | 'bold';
  color?: 'primary' | 'secondary' | 'tertiary' | 'success' | 'warning' | 'error' | 'inherit';
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

export const Text: React.FC<EnhancedTextProps> = ({
  variant = 'body',
  weight = 'normal',
  color = 'inherit',
  className = '',
  style = {},
  children,
  ...props
}) => {
  const getStyle = (): React.CSSProperties => {
    return {
      fontSize: getFontSize(),
      fontWeight: getFontWeight(),
      lineHeight: getLineHeight(),
      letterSpacing: getLetterSpacing(),
      color: getColor(),
      textTransform: getTextTransform(),
      ...style,
    };
  };

  const getFontSize = () => {
    switch (variant) {
      case 'caption':
        return '12px';
      case 'overline':
        return '11px';
      case 'label':
        return '13px';
      default:
        return '14px';
    }
  };

  const getFontWeight = () => {
    switch (weight) {
      case 'light':
        return 300;
      case 'normal':
        return 400;
      case 'medium':
        return 500;
      case 'semibold':
        return 600;
      case 'bold':
        return 700;
      default:
        return 400;
    }
  };

  const getLineHeight = () => {
    switch (variant) {
      case 'caption':
        return 1.4;
      case 'overline':
        return 1.5;
      case 'label':
        return 1.3;
      default:
        return 1.5;
    }
  };

  const getLetterSpacing = () => {
    switch (variant) {
      case 'overline':
        return '0.08em';
      case 'label':
        return '0.01em';
      default:
        return 'normal';
    }
  };

  const getTextTransform = () => {
    switch (variant) {
      case 'overline':
        return 'uppercase' as const;
      default:
        return 'none' as const;
    }
  };

  const getColor = () => {
    switch (color) {
      case 'primary':
        return '#262626';
      case 'secondary':
        return '#8c8c8c';
      case 'tertiary':
        return '#bfbfbf';
      case 'success':
        return '#389e0d';
      case 'warning':
        return '#d48806';
      case 'error':
        return '#cf1322';
      default:
        return 'inherit';
    }
  };

  return (
    <AntText
      className={`enhanced-text ${className}`}
      style={getStyle()}
    >
      {children}
    </AntText>
  );
};

// Enhanced Paragraph Component
interface EnhancedParagraphProps {
  variant?: 'body' | 'lead' | 'small';
  spacing?: 'tight' | 'normal' | 'relaxed';
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

export const Paragraph: React.FC<EnhancedParagraphProps> = ({
  variant = 'body',
  spacing = 'normal',
  className = '',
  style = {},
  children,
  ...props
}) => {
  const getStyle = (): React.CSSProperties => {
    return {
      fontSize: getFontSize(),
      lineHeight: getLineHeight(),
      marginBottom: getMarginBottom(),
      color: '#262626',
      ...style,
    };
  };

  const getFontSize = () => {
    switch (variant) {
      case 'lead':
        return '16px';
      case 'small':
        return '12px';
      default:
        return '14px';
    }
  };

  const getLineHeight = () => {
    switch (spacing) {
      case 'tight':
        return 1.4;
      case 'relaxed':
        return 1.7;
      default:
        return 1.5;
    }
  };

  const getMarginBottom = () => {
    switch (variant) {
      case 'lead':
        return '20px';
      case 'small':
        return '12px';
      default:
        return '16px';
    }
  };

  return (
    <AntParagraph
      className={`enhanced-paragraph ${className}`}
      style={getStyle()}
    >
      {children}
    </AntParagraph>
  );
};

// Export as default object for easier importing
const Typography = {
  Title,
  Text,
  Paragraph,
};

export default Typography;