/**
 * HTTP API Client
 * 封装基础的 fetch 请求
 */

// 使用环境变量作为 API 基础路径，如果没有配置则默认为空（相对路径）
const API_BASE = import.meta.env.VITE_API_TARGET || '';

export class ApiError extends Error {
  public status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, options);

  if (!response.ok) {
    throw new ApiError(response.status, `Request failed: ${response.statusText}`);
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
  }
};

