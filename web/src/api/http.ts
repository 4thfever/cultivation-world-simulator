/**
 * HTTP API Client
 * 封装基础的 fetch 请求
 */

// 使用环境变量作为 API 基础路径，如果没有配置则默认为空（相对路径）
const API_BASE = import.meta.env.VITE_API_TARGET || '';
const DEFAULT_TIMEOUT_MS = 30000;
const REQUEST_TIMEOUT_REASON = 'cws-request-timeout';

export interface HttpRequestOptions {
  timeoutMs?: number;
  signal?: AbortSignal;
}

export class ApiError extends Error {
  public status: number;
  public response: { data: unknown };

  constructor(status: number, message: string, responseData?: unknown) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
    this.response = { data: responseData || {} };
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  requestOptions: HttpRequestOptions = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const controller = new AbortController();
  const timeoutMs = requestOptions.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  let didTimeout = false;
  const callerSignal = requestOptions.signal ?? options.signal;
  const abortFromCaller = () => {
    controller.abort(callerSignal?.reason);
  };
  const timeout = globalThis.setTimeout(() => {
    didTimeout = true;
    controller.abort(REQUEST_TIMEOUT_REASON);
  }, timeoutMs);

  if (callerSignal) {
    if (callerSignal.aborted) {
      abortFromCaller();
    } else {
      callerSignal.addEventListener('abort', abortFromCaller, { once: true });
    }
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError' && didTimeout) {
      throw new ApiError(408, `Request timed out after ${Math.round(timeoutMs / 1000)}s`);
    }
    throw error;
  } finally {
    globalThis.clearTimeout(timeout);
    callerSignal?.removeEventListener('abort', abortFromCaller);
  }

  if (!response.ok) {
    // 尝试解析错误响应的 JSON
    let errorData: unknown = null;
    let errorMessage = `Request failed: ${response.statusText}`;
    
    try {
      errorData = await response.json();
      // 如果后端返回了 detail 字段，使用它作为错误消息
      if (errorData && typeof errorData === 'object' && 'detail' in errorData) {
        const detail = (errorData as { detail?: unknown }).detail;
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (
          detail &&
          typeof detail === 'object' &&
          'message' in detail &&
          typeof (detail as { message?: unknown }).message === 'string'
        ) {
          errorMessage = (detail as { message: string }).message;
        }
      }
    } catch {
      // 如果解析失败，使用默认错误消息
    }
    
    throw new ApiError(response.status, errorMessage, errorData);
  }

  // 假设后端总是返回 JSON
  const data: unknown = await response.json();
  if (
    data &&
    typeof data === 'object' &&
    'ok' in data &&
    data.ok === true &&
    'data' in data
  ) {
    return (data as { data: T }).data;
  }
  return data as T;
}

export const httpClient = {
  get<T>(path: string) {
    return request<T>(path, { method: 'GET' });
  },

  post<T>(path: string, body: unknown, options?: HttpRequestOptions) {
    return request<T>(path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }, options);
  },

  patch<T>(path: string, body: unknown, options?: HttpRequestOptions) {
    return request<T>(path, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }, options);
  },

  put<T>(path: string, body: unknown, options?: HttpRequestOptions) {
    return request<T>(path, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }, options);
  },

  delete<T>(path: string) {
    return request<T>(path, { method: 'DELETE' });
  }
};

