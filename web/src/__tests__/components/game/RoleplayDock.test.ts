import { mount } from '@vue/test-utils'
import { reactive, nextTick } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import RoleplayDock from '@/components/game/RoleplayDock.vue'

const { eventApiMock } = vi.hoisted(() => ({
  eventApiMock: {
    fetchEvents: vi.fn(async () => ({ events: [] })),
  },
}))

const roleplayStoreMock = reactive({
  session: {
    controlled_avatar_id: null as string | null,
    status: 'inactive',
    pending_request: null as null | {
      request_id: string
      type: string
      avatar_id: string
      title: string
      description: string
      options?: Array<{ key: string; title: string; description: string }>
      messages?: Array<{ id: string; role: string; speaker_name: string; content: string; created_at: number }>
    },
    last_prompt_context: null as Record<string, unknown> | null,
    conversation_session: null as null | {
      messages: Array<{ id: string; role: string; speaker_name: string; content: string; created_at: number }>
    },
    interaction_history: [] as Array<Record<string, unknown>>,
  },
  isSubmitting: false,
  error: null as string | null,
  fetchSession: vi.fn(async () => roleplayStoreMock.session),
  submitDecision: vi.fn(async () => ({ status: 'ok' })),
  submitChoice: vi.fn(async () => ({ status: 'ok' })),
  sendConversation: vi.fn(async () => ({ status: 'ok' })),
  endConversation: vi.fn(async () => ({ status: 'ok' })),
  stopRoleplay: vi.fn(async () => ({
    controlled_avatar_id: null,
    status: 'inactive',
    pending_request: null,
    last_prompt_context: null,
  })),
})

vi.mock('@/stores/roleplay', () => ({
  useRoleplayStore: () => roleplayStoreMock,
}))

vi.mock('@/api', () => ({
  eventApi: eventApiMock,
}))

vi.mock('@/api/mappers/event', () => ({
  mapEventDtosToTimeline: vi.fn((events: unknown[]) => events),
}))

vi.mock('@/utils/appError', () => ({
  logError: vi.fn(),
}))

describe('RoleplayDock', () => {
  beforeEach(() => {
    roleplayStoreMock.session.controlled_avatar_id = null
    roleplayStoreMock.session.status = 'inactive'
    roleplayStoreMock.session.pending_request = null
    roleplayStoreMock.session.last_prompt_context = null
    roleplayStoreMock.session.conversation_session = null
    roleplayStoreMock.session.interaction_history = []
    roleplayStoreMock.isSubmitting = false
    roleplayStoreMock.error = null
    roleplayStoreMock.fetchSession.mockClear()
    roleplayStoreMock.submitDecision.mockClear()
    roleplayStoreMock.submitChoice.mockClear()
    roleplayStoreMock.sendConversation.mockClear()
    roleplayStoreMock.endConversation.mockClear()
    roleplayStoreMock.stopRoleplay.mockClear()
    eventApiMock.fetchEvents.mockClear()
    eventApiMock.fetchEvents.mockResolvedValue({ events: [] })
  })

  it('renders decision console and submits command text', async () => {
    roleplayStoreMock.session.controlled_avatar_id = 'avatar-1'
    roleplayStoreMock.session.status = 'awaiting_decision'
    roleplayStoreMock.session.pending_request = {
      request_id: 'req-1',
      type: 'decision',
      avatar_id: 'avatar-1',
      title: '闻人雾 需要新的指令',
      description: '世界已暂停，正在等待你的扮演指令。',
    }
    roleplayStoreMock.session.last_prompt_context = {
      avatar_name: '闻人雾',
    }
    roleplayStoreMock.session.interaction_history = [
      { type: 'command', created_at: 1, text: '先调息恢复，再去探索。' },
      {
        type: 'action_chain',
        created_at: 2,
        actions: [{ action_name: 'MoveToRegion', tokens: [{ kind: 'verb', text: '移动到' }, { kind: 'arg', text: '青石谷' }] }],
      },
    ]

    const wrapper = mount(RoleplayDock)
    await nextTick()

    expect(wrapper.text()).toContain('闻人雾')
    expect(wrapper.text()).toContain('等待指令')
    expect(wrapper.text()).toContain('青石谷')

    const textarea = wrapper.find('textarea.roleplay-dock__input')
    expect(textarea.exists()).toBe(true)
    await textarea.setValue('先调息恢复，再去探索。')
    await wrapper.find('button.roleplay-dock__submit').trigger('click')

    expect(roleplayStoreMock.submitDecision).toHaveBeenCalledWith({
      avatar_id: 'avatar-1',
      request_id: 'req-1',
      command_text: '先调息恢复，再去探索。',
    })
  })

  it('renders choice buttons and submits selected option', async () => {
    roleplayStoreMock.session.controlled_avatar_id = 'avatar-1'
    roleplayStoreMock.session.status = 'awaiting_choice'
    roleplayStoreMock.session.pending_request = {
      request_id: 'req-choice',
      type: 'choice',
      avatar_id: 'avatar-1',
      title: '是否赴约',
      description: '对方正在等待你的回应。',
      options: [
        { key: 'accept', title: '接受', description: '前往会面' },
        { key: 'reject', title: '拒绝', description: '婉拒邀约' },
      ],
    }
    roleplayStoreMock.session.last_prompt_context = {
      avatar_name: '闻人雾',
    }
    roleplayStoreMock.session.interaction_history = [
      { type: 'choice', created_at: 1, text: '拒绝：婉拒邀约' },
    ]

    const wrapper = mount(RoleplayDock)
    await nextTick()

    expect(wrapper.text()).toContain('拒绝：婉拒邀约')
    const buttons = wrapper.findAll('button.roleplay-dock__choice')
    expect(buttons).toHaveLength(2)
    await buttons[1].trigger('click')

    expect(roleplayStoreMock.submitChoice).toHaveBeenCalledWith({
      avatar_id: 'avatar-1',
      request_id: 'req-choice',
      selected_key: 'reject',
    })
  })

  it('supports resize drag on the dock handle', async () => {
    roleplayStoreMock.session.controlled_avatar_id = 'avatar-1'
    roleplayStoreMock.session.status = 'observing'
    roleplayStoreMock.session.last_prompt_context = {
      avatar_name: '闻人雾',
    }

    const wrapper = mount(RoleplayDock, {
      attachTo: document.body,
    })
    await nextTick()

    expect((wrapper.element as HTMLElement).style.height).toBe('214px')

    await wrapper.find('.roleplay-dock__resize-handle').trigger('mousedown', {
      clientY: 300,
      preventDefault: () => {},
    })
    document.dispatchEvent(new MouseEvent('mousemove', { clientY: 250 }))
    await nextTick()

    expect((wrapper.element as HTMLElement).style.height).toBe('264px')

    document.dispatchEvent(new MouseEvent('mouseup'))
    await nextTick()

    wrapper.unmount()
  })

  it('renders conversation mode and sends chat messages', async () => {
    roleplayStoreMock.session.controlled_avatar_id = 'avatar-1'
    roleplayStoreMock.session.status = 'conversing'
    roleplayStoreMock.session.pending_request = {
      request_id: 'req-conversation',
      type: 'conversation',
      avatar_id: 'avatar-1',
      target_avatar_id: 'avatar-2',
      title: '闻人雾 与 阴长生 对话中',
      description: '世界已暂停，等待你继续发言。',
      messages: [
        { id: 'm1', role: 'assistant', speaker_name: '阴长生', content: '阁下为何前来？', created_at: 1 },
      ],
    }
    roleplayStoreMock.session.conversation_session = {
      messages: [
        { id: 'm1', role: 'assistant', speaker_name: '阴长生', content: '阁下为何前来？', created_at: 1 },
      ],
    }
    roleplayStoreMock.session.last_prompt_context = {
      avatar_name: '闻人雾',
      target_avatar_name: '阴长生',
    }
    roleplayStoreMock.session.interaction_history = [
      { type: 'conversation_player', created_at: 1, text: '我来求一条路。' },
      { type: 'conversation_assistant', created_at: 2, text: '阁下为何前来？' },
    ]

    const wrapper = mount(RoleplayDock)
    await nextTick()

    expect(wrapper.text()).toContain('闻人雾 ↔ 阴长生')
    expect(wrapper.text()).toContain('阁下为何前来？')
    expect(wrapper.text()).toContain('我来求一条路。')

    const textarea = wrapper.find('.roleplay-dock__input--conversation')
    await textarea.setValue('我来求一条路。')
    await wrapper.find('.roleplay-dock__conversation-actions .roleplay-dock__submit').trigger('click')

    expect(roleplayStoreMock.sendConversation).toHaveBeenCalledWith({
      avatar_id: 'avatar-1',
      request_id: 'req-conversation',
      message: '我来求一条路。',
    })
  })
})
