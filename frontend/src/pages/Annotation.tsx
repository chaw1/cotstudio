import React from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Typography, Alert } from 'antd';
import { useResponsiveBreakpoint } from '../hooks/useResponsiveBreakpoint';
import AnnotationWorkspace from '../components/annotation/AnnotationWorkspace';

const { Title } = Typography;

const Annotation: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams] = useSearchParams();
  const sliceId = searchParams.get('sliceId');
  const { isMobile, isTablet } = useResponsiveBreakpoint();

  if (!projectId) {
    return (
      <div style={{ padding: isMobile ? '16px' : '24px' }}>
        <Alert
          message="错误"
          description="缺少项目ID参数"
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div style={{ 
      height: '100%', 
      overflow: 'hidden'
    }}>
      <AnnotationWorkspace 
        projectId={projectId} 
        sliceId={sliceId || undefined}
      />
    </div>
  );
};

export default Annotation;