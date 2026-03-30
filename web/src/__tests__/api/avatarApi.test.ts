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

  it('posts custom content generation requests', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok', draft: {} })

    await avatarApi.generateCustomContent({
      category: 'weapon',
      realm: 'CORE_FORMATION',
      user_prompt: '想要一把金丹剑',
    })

    expect(postMock).toHaveBeenCalledWith('/api/action/generate_custom_content', {
      category: 'weapon',
      realm: 'CORE_FORMATION',
      user_prompt: '想要一把金丹剑',
    })
  })

  it('posts custom content creation requests', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok', item: {} })

    await avatarApi.createCustomContent({
      category: 'auxiliary',
      draft: {
        id: '0',
        category: 'auxiliary',
        realm: 'CORE_FORMATION',
        name: '草稿',
        effects: { extra_max_hp: 30 },
      } as any,
    })

    expect(postMock).toHaveBeenCalledWith('/api/action/create_custom_content', {
      category: 'auxiliary',
      draft: {
        id: '0',
        category: 'auxiliary',
        realm: 'CORE_FORMATION',
        name: '草稿',
        effects: { extra_max_hp: 30 },
      },
    })
  })

  it('allows technique custom generation without realm', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok', draft: {} })

    await avatarApi.generateCustomContent({
      category: 'technique',
      user_prompt: '我想要一本偏火属性的功法',
    })

    expect(postMock).toHaveBeenCalledWith('/api/action/generate_custom_content', {
      category: 'technique',
      user_prompt: '我想要一本偏火属性的功法',
    })
  })
})
