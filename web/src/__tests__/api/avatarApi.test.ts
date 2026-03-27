import { beforeEach, describe, expect, it, vi } from 'vitest'

const getMock = vi.fn()
const postMock = vi.fn()

vi.mock('@/api/http', () => ({
  httpClient: {
    get: getMock,
    post: postMock,
  },
}))

describe('avatarApi', () => {
  beforeEach(() => {
    getMock.mockReset()
    postMock.mockReset()
  })

  it('fetches avatar adjust options from the dedicated endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    getMock.mockResolvedValue({ techniques: [], weapons: [], auxiliaries: [], personas: [] })

    await avatarApi.fetchAvatarAdjustOptions()

    expect(getMock).toHaveBeenCalledWith('/api/meta/avatar_adjust_options')
  })

  it('posts avatar adjustment payloads through the unified endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.updateAvatarAdjustment({
      avatar_id: 'avatar_1',
      category: 'personas',
      persona_ids: [1, 2, 3],
    })

    expect(postMock).toHaveBeenCalledWith('/api/action/update_avatar_adjustment', {
      avatar_id: 'avatar_1',
      category: 'personas',
      persona_ids: [1, 2, 3],
    })
  })
})
