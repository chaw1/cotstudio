import { useEffect } from 'react';
import { App } from 'antd';
import { setAppInstance } from '../utils/message';

export const useAppMessage = () => {
  const app = App.useApp();
  
  useEffect(() => {
    // 设置App实例到message工具中
    setAppInstance(app);
  }, [app]);
  
  return app;
};

export default useAppMessage;