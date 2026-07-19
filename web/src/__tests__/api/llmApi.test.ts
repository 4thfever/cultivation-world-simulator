import { beforeEach, describe, expect, it, vi } from 'vitest'

const getMock = vi.fn()
const postMock = vi.fn()
const putMock = vi.fn()

vi.mock('@/api/http', () => ({
  httpClient: {
    get: getMock,
    post: postMock,
    put: putMock,
  },
}))

describe('llmApi', () => {
  beforeEach(() => {
    getMock.mockReset()
    postMock.mockReset()
    putMock.mockReset()
  })

  it('uses a long timeout for connectivity tests', async () => {
    const { llmApi } = await import('@/api/modules/llm')
    const config = {
      base_url: 'http://localhost:11434/v1',
      api_key: '',
      model_name: 'qwen3.5:9b',
      fast_model_name: 'qwen3:8b',
      mode: 'default',
      max_concurrent_requests: 8,
      api_format: 'openai',
    }
    postMock.mockResolvedValue({ status: 'ok' })

    await llmApi.testConnection(config)

    expect(postMock).toHaveBeenCalledWith(
      '/api/settings/llm/test',
      config,
      { timeoutMs: 150000 },
    )
  })
})
