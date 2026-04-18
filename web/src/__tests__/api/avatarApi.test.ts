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
    getMock.mockResolvedValue({ techniques: [], weapons: [], auxiliaries: [], personas: [], goldfingers: [] })

    await avatarApi.fetchAvatarAdjustOptions()

    expect(getMock).toHaveBeenCalledWith('/api/v1/query/meta/avatar-adjust-options')
  })

  it('posts avatar adjustment payloads through the unified endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.updateAvatarAdjustment({
      avatar_id: 'avatar_1',
      category: 'personas',
      persona_ids: [1, 2, 3],
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/update-adjustment', {
      avatar_id: 'avatar_1',
      category: 'personas',
      persona_ids: [1, 2, 3],
    })
  })

  it('posts goldfinger adjustment payloads through the unified endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.updateAvatarAdjustment({
      avatar_id: 'avatar_1',
      category: 'goldfinger',
      target_id: 930001,
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/update-adjustment', {
      avatar_id: 'avatar_1',
      category: 'goldfinger',
      target_id: 930001,
    })
  })

  it('posts avatar portrait update payloads through the dedicated endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.updateAvatarPortrait({
      avatar_id: 'avatar_1',
      pic_id: 12,
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/update-portrait', {
      avatar_id: 'avatar_1',
      pic_id: 12,
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

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/generate-custom-content', {
      category: 'weapon',
      realm: 'CORE_FORMATION',
      user_prompt: '想要一把金丹剑',
    })
  })

  it('posts custom goldfinger generation requests without realm', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok', draft: {} })

    await avatarApi.generateCustomContent({
      category: 'goldfinger',
      user_prompt: '想要一个偏签到流的外挂',
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/generate-custom-content', {
      category: 'goldfinger',
      user_prompt: '想要一个偏签到流的外挂',
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

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/create-custom-content', {
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

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/generate-custom-content', {
      category: 'technique',
      user_prompt: '我想要一本偏火属性的功法',
    })
  })

  it('fetches avatar meta from /api/v1', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    getMock.mockResolvedValue({ males: [1, 2], females: [3, 4] })

    await avatarApi.fetchAvatarMeta()

    expect(getMock).toHaveBeenCalledWith('/api/v1/query/meta/avatars')
  })

  it('fetches roleplay session from the dedicated endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    getMock.mockResolvedValue({ controlled_avatar_id: null, status: 'inactive', pending_request: null, last_prompt_context: null })

    await avatarApi.fetchRoleplaySession()

    expect(getMock).toHaveBeenCalledWith('/api/v1/query/roleplay/session')
  })

  it('posts roleplay decision submissions', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok', planned_action_count: 1 })

    await avatarApi.submitRoleplayDecision({
      avatar_id: 'avatar_1',
      request_id: 'req_1',
      command_text: '先调息恢复一下',
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/roleplay/submit-decision', {
      avatar_id: 'avatar_1',
      request_id: 'req_1',
      command_text: '先调息恢复一下',
    })
  })

  it('posts roleplay choice submissions', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.submitRoleplayChoice({
      avatar_id: 'avatar_1',
      request_id: 'req_choice_1',
      selected_key: 'ACCEPT',
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/roleplay/submit-choice', {
      avatar_id: 'avatar_1',
      request_id: 'req_choice_1',
      selected_key: 'ACCEPT',
    })
  })

  it('posts roleplay conversation messages', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok', messages: [], reply: '回应' })

    await avatarApi.sendRoleplayConversation({
      avatar_id: 'avatar_1',
      request_id: 'req_conv_1',
      message: '你好',
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/roleplay/conversation/send', {
      avatar_id: 'avatar_1',
      request_id: 'req_conv_1',
      message: '你好',
    })
  })

  it('posts roleplay conversation end requests', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok', summary: '二人谈笑风生。' })

    await avatarApi.endRoleplayConversation({
      avatar_id: 'avatar_1',
      request_id: 'req_conv_1',
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/roleplay/conversation/end', {
      avatar_id: 'avatar_1',
      request_id: 'req_conv_1',
    })
  })
})
