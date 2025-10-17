import { useState, useCallback } from 'react';
import { message } from 'antd';
import { ApiError } from '../types';

interface UseApiOptions {
  showSuccessMessage?: boolean;
  showErrorMessage?: boolean;
  successMessage?: string;
}

interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  execute: (...args: any[]) => Promise<T | null>;
  reset: () => void;
}

function useApi<T = any>(
  apiFunction: (...args: any[]) => Promise<T>,
  options: UseApiOptions = {}
): UseApiReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const {
    showSuccessMessage = false,
    showErrorMessage = true,
    successMessage = '操作成功',
  } = options;

  const execute = useCallback(
    async (...args: any[]): Promise<T | null> => {
      try {
        setLoading(true);
        setError(null);
        
        const result = await apiFunction(...args);
        setData(result);
        
        if (showSuccessMessage) {
          message.success(successMessage);
        }
        
        return result;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError);
        
        if (showErrorMessage) {
          message.error(apiError.message || '操作失败');
        }
        
        return null;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, showSuccessMessage, showErrorMessage, successMessage]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset,
  };
}

export default useApi;