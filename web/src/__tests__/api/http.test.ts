import { describe, it, expect, vi, beforeEach } from 'vitest'
import { httpClient } from '@/api/http'

describe('httpClient api', () => {
  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ data: 'test' })
    }) as any
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
})
