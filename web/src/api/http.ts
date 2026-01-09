/**
 * HTTP API Client
 * 封装基础的 fetch 请求
 */

// 使用环境变量作为 API 基础路径，如果没有配置则默认为空（相对路径）
const API_BASE = import.meta.env.VITE_API_TARGET || '';

export class ApiError extends Error {
  public status: number;
  public response: { data: any };

  constructor(status: number, message: string, responseData?: any) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
    this.response = { data: responseData || {} };
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, options);

  if (!response.ok) {
    // 尝试解析错误响应的 JSON
    let errorData = null;
    let errorMessage = `Request failed: ${response.statusText}`;
    
    try {
      errorData = await response.json();
      // 如果后端返回了 detail 字段，使用它作为错误消息
      if (errorData?.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // 如果解析失败，使用默认错误消息
    }
    
    throw new ApiError(response.status, errorMessage, errorData);
  }

  // 假设后端总是返回 JSON
  return response.json();
}

export const httpClient = {
  get<T>(path: string) {
    return request<T>(path, { method: 'GET' });
  },

  post<T>(path: string, body: unknown) {
    return request<T>(path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
  },

  delete<T>(path: string) {
    return request<T>(path, { method: 'DELETE' });
  }
};

