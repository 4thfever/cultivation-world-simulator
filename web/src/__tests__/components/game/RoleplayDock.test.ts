import { mount } from '@vue/test-utils'
import { reactive, nextTick } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createI18n } from 'vue-i18n'

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

function createRoleplayI18n() {
  return createI18n({
    legacy: false,
    locale: 'zh',
    messages: {
      zh: {
        game: {
          roleplay: {
            panel: { stop: '退出扮演' },
            dock: {
              interaction_title: '交互流',
              interaction_caption: '本次扮演中的输入与输出',
              interaction_empty: '当前还没有新的交互记录。',
            },
            status: {
              awaiting_decision: '等待指令',
              awaiting_choice: '等待选择',
              conversing: '对话中',
              submitting: '提交中',
              observing: '观察中',
            },
            summary: {
              decision: '需要决定下一步行动',
              choice: '需要做出回应',
              conversation: '正在与 {target} 交谈',
              observing: '当前动作链仍在执行',
            },
            request: {
              title_decision: '决策',
              title_choice: '选项',
              title_conversation: '对话',
              title_observing: '观察',
              caption_decision: '输入一句意图，系统会扩展成行动链',
              caption_choice: '从有限选项里做出一次回应',
              caption_conversation: '玩家控制 {avatar} 发言，对方由 LLM 回复',
              caption_observing: '当前没有需要立即处理的请求',
              decision_default_description: '输入一句意图，系统会把它扩展成该角色的下一步行动链。',
              choice_default_description: '请选择一个回应。',
              conversation_default_description: '世界已暂停，等待你继续扮演当前角色发言。',
            },
            decision: {
              placeholder: '输入角色的下一步意图，例如：先调息恢复，再去附近探索。',
              submit: '提交指令',
              submitting: '处理中...',
            },
            choice: {
              submitting: '正在处理选择，请稍候...',
            },
            conversation: {
              placeholder: '输入你想说的话。',
              submit: '发送',
              sending: '发送中...',
              awaiting_reply: '等待回复...',
              end: '结束对话',
            },
            idle: {
              hint: '当前仍在上帝视角观察世界。该角色的动作链结束后，会在这里等待你的下一步操作。',
            },
            fallback: {
              avatar_name: '角色',
              counterpart_name: '对方',
            },
          },
        },
      },
    },
  })
}

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

    const wrapper = mount(RoleplayDock, { global: { plugins: [createRoleplayI18n()] } })
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
      { type: 'choice_prompt', created_at: 1, text: '冷清雅邀请你加入浩然书院，成为门下弟子。' },
      { type: 'choice', created_at: 1, text: '拒绝：婉拒邀约' },
    ]

    const wrapper = mount(RoleplayDock, { global: { plugins: [createRoleplayI18n()] } })
    await nextTick()

    expect(wrapper.text()).toContain('冷清雅邀请你加入浩然书院，成为门下弟子。')
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
      global: { plugins: [createRoleplayI18n()] },
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

  it('keeps interaction history visible while observing', async () => {
    roleplayStoreMock.session.controlled_avatar_id = 'avatar-1'
    roleplayStoreMock.session.status = 'observing'
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

    const wrapper = mount(RoleplayDock, { global: { plugins: [createRoleplayI18n()] } })
    await nextTick()

    expect(wrapper.text()).toContain('当前仍在上帝视角观察世界')
    expect(wrapper.text()).toContain('先调息恢复，再去探索。')
    expect(wrapper.text()).toContain('移动到')
    expect(wrapper.text()).toContain('青石谷')
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

    const wrapper = mount(RoleplayDock, { global: { plugins: [createRoleplayI18n()] } })
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

  it('shows optimistic player message while waiting for conversation reply', async () => {
    let resolveSend: (() => void) | null = null
    roleplayStoreMock.sendConversation.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveSend = () => resolve({ status: 'ok' })
        })
    )

    roleplayStoreMock.session.controlled_avatar_id = 'avatar-1'
    roleplayStoreMock.session.status = 'conversing'
    roleplayStoreMock.session.pending_request = {
      request_id: 'req-conversation',
      type: 'conversation',
      avatar_id: 'avatar-1',
      target_avatar_id: 'avatar-2',
      title: '闻人雾 与 阴长生 对话中',
      description: '世界已暂停，等待你继续发言。',
      messages: [],
    }
    roleplayStoreMock.session.conversation_session = {
      messages: [],
    }
    roleplayStoreMock.session.last_prompt_context = {
      avatar_name: '闻人雾',
      target_avatar_name: '阴长生',
    }

    const wrapper = mount(RoleplayDock, { global: { plugins: [createRoleplayI18n()] } })
    await nextTick()

    const textarea = wrapper.find('.roleplay-dock__input--conversation')
    await textarea.setValue('你好')
    await wrapper.find('.roleplay-dock__conversation-actions .roleplay-dock__submit').trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('你好')
    expect(wrapper.text()).toContain('等待回复...')

    resolveSend?.()
    await nextTick()
    await nextTick()
  })
})
