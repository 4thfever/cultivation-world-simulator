const DEFAULT_TIMEOUT = 10000

export interface ApiRequestOptions extends RequestInit {
  timeout?: number
}

export async function apiGet<T>(url: string, options: ApiRequestOptions = {}): Promise<T> {
  const { timeout = DEFAULT_TIMEOUT, ...init } = options
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, { ...init, signal: controller.signal })
    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`)
    }
    return (await response.json()) as T
  } finally {
    window.clearTimeout(timer)
  }
}

export async function apiPost<T>(url: string, body: any, options: ApiRequestOptions = {}): Promise<T> {
  const { timeout = DEFAULT_TIMEOUT, headers, ...init } = options
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...headers
      },
      body: JSON.stringify(body),
      signal: controller.signal,
      ...init
    })
    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`)
    }
    return (await response.json()) as T
  } finally {
    window.clearTimeout(timer)
  }
}
