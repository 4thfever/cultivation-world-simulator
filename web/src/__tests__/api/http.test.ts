import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ApiError, httpClient } from '@/api/http'

describe('httpClient api', () => {
  beforeEach(() => {
    vi.useRealTimers()
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ data: 'test' })
    }) as any
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should make GET request successfully', async () => {
    const res = await httpClient.get('/test')
    expect(res).toEqual({ data: 'test' })
  })

  it('should unwrap v1 ok/data envelope automatically', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ ok: true, data: { value: 42 } })
    }) as any

    const res = await httpClient.get('/test')
    expect(res).toEqual({ value: 42 })
  })

  it('should make POST request successfully', async () => {
    const res = await httpClient.post('/test', { data: 1 })
    expect(res).toEqual({ data: 'test' })
  })

  it('should throw error on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: vi.fn().mockResolvedValue({ error: 'Not Found' })
    }) as any

    await expect(httpClient.get('/test')).rejects.toThrow()
  })

  it('should prefer structured detail.message on v1 error payloads', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: vi.fn().mockResolvedValue({ detail: { code: 'WORLD_NOT_READY', message: 'World not initialized' } })
    }) as any

    await expect(httpClient.get('/test')).rejects.toThrow('World not initialized')
  })

  it('should throw error when fetch fails', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error')) as any

    await expect(httpClient.get('/test')).rejects.toThrow('Network error')
  })

  it('uses custom timeout values for long-running requests', async () => {
    vi.useFakeTimers()
    global.fetch = vi.fn((_url: string, init?: RequestInit) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => {
        reject(new DOMException('Aborted', 'AbortError'))
      })
    })) as any

    const requestPromise = httpClient.post('/slow', { data: 1 }, { timeoutMs: 120000 })
    const expectation = expect(requestPromise).rejects.toMatchObject<ApiError>({
      status: 408,
      message: 'Request timed out after 120s',
    })

    await vi.advanceTimersByTimeAsync(120000)

    await expectation
  })

  it('still applies timeout when a caller signal is provided', async () => {
    vi.useFakeTimers()
    const callerController = new AbortController()
    global.fetch = vi.fn((_url: string, init?: RequestInit) => new Promise((_resolve, reject) => {
      expect(init?.signal).not.toBe(callerController.signal)
      init?.signal?.addEventListener('abort', () => {
        reject(new DOMException('Aborted', 'AbortError'))
      })
    })) as any

    const requestPromise = httpClient.post(
      '/slow-with-signal',
      { data: 1 },
      { timeoutMs: 5000, signal: callerController.signal },
    )
    const expectation = expect(requestPromise).rejects.toMatchObject<ApiError>({
      status: 408,
      message: 'Request timed out after 5s',
    })

    await vi.advanceTimersByTimeAsync(5000)

    await expectation
  })

  it('does not report caller aborts as request timeouts', async () => {
    vi.useFakeTimers()
    const callerController = new AbortController()
    global.fetch = vi.fn((_url: string, init?: RequestInit) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener('abort', () => {
        reject(new DOMException('Aborted', 'AbortError'))
      })
    })) as any

    const requestPromise = httpClient.post(
      '/caller-abort',
      { data: 1 },
      { timeoutMs: 5000, signal: callerController.signal },
    )

    callerController.abort()

    await expect(requestPromise).rejects.toMatchObject({
      name: 'AbortError',
    })
  })
})
