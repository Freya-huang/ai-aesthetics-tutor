import axios, { AxiosError, AxiosInstance } from 'axios';
import type { ApiError } from '@/types';

const client: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    let message = '请求失败，请稍后重试';
    if (error.response) {
      const data = error.response.data;
      if (data?.detail) {
        message = data.detail;
      } else if (data?.message) {
        message = data.message;
      } else if (error.response.status === 404) {
        message = '请求的资源不存在';
      } else if (error.response.status >= 500) {
        message = '服务器错误，请稍后重试';
      }
    } else if (error.code === 'ECONNABORTED') {
      message = '请求超时，请检查网络连接';
    } else if (error.message === 'Network Error') {
      message = '网络连接失败，请检查后端服务是否启动';
    }
    const enhancedError = new Error(message) as Error & { originalError?: AxiosError; status?: number };
    enhancedError.originalError = error;
    enhancedError.status = error.response?.status;
    return Promise.reject(enhancedError);
  }
);

export default client;
