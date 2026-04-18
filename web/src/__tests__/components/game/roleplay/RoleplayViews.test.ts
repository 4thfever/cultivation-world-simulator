import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import RoleplayChoiceView from '@/components/game/roleplay/RoleplayChoiceView.vue'
import RoleplayConversationView from '@/components/game/roleplay/RoleplayConversationView.vue'
import RoleplayDecisionView from '@/components/game/roleplay/RoleplayDecisionView.vue'
import RoleplayDockHeader from '@/components/game/roleplay/RoleplayDockHeader.vue'
import RoleplayIdleView from '@/components/game/roleplay/RoleplayIdleView.vue'
import RoleplayInteractionHistory from '@/components/game/roleplay/RoleplayInteractionHistory.vue'
import RoleplaySectionHeader from '@/components/game/roleplay/RoleplaySectionHeader.vue'

describe('Roleplay subviews', () => {
  it('renders dock header and emits exit', async () => {
    const wrapper = mount(RoleplayDockHeader, {
      props: {
        avatarName: '闻人雾',
        statusText: '等待指令',
        requestSummary: '需要决定下一步行动',
        isSubmitting: false,
      },
    })

    expect(wrapper.text()).toContain('闻人雾')
    expect(wrapper.text()).toContain('等待指令')
    expect(wrapper.text()).toContain('需要决定下一步行动')

    await wrapper.find('button.roleplay-dock__exit').trigger('click')
    expect(wrapper.emitted('exit')).toHaveLength(1)
  })

  it('renders section header copy', () => {
    const wrapper = mount(RoleplaySectionHeader, {
      props: {
        title: '决策',
        caption: '输入一句意图，系统会扩展成行动链',
      },
    })

    expect(wrapper.text()).toContain('决策')
    expect(wrapper.text()).toContain('输入一句意图，系统会扩展成行动链')
  })

  it('updates and submits decision input', async () => {
    const wrapper = mount(RoleplayDecisionView, {
      props: {
        description: '输入一句意图。',
        modelValue: '',
        errorText: '',
        isSubmitting: false,
        submitText: '提交指令',
        interactionHistory: [
          { type: 'command', created_at: 1, text: '先恢复灵气。' },
          {
            type: 'action_chain',
            created_at: 2,
            actions: [
              {
                action_name: 'Respire',
                tokens: [
                  { kind: 'verb', text: '调息' },
                  { kind: 'arg', text: '片刻' },
                ],
              },
            ],
          },
        ],
      },
    })

    expect(wrapper.text()).toContain('先恢复灵气。')
    expect(wrapper.text()).toContain('调息')
    expect(wrapper.text()).toContain('片刻')

    const textarea = wrapper.find('textarea.roleplay-dock__input')
    await textarea.setValue('先恢复灵气。')

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['先恢复灵气。'])

    await wrapper.setProps({ modelValue: '先恢复灵气。' })
    await wrapper.find('button.roleplay-dock__submit').trigger('click')

    expect(wrapper.emitted('submit')).toHaveLength(1)
  })

  it('renders choices and emits selected key', async () => {
    const wrapper = mount(RoleplayChoiceView, {
      props: {
        description: '请选择一个回应。',
        options: [
          { key: 'accept', title: '接受', description: '前往会面' },
          { key: 'reject', title: '拒绝', description: '婉拒邀约' },
        ],
        errorText: '',
        isSubmitting: false,
        submittingText: '',
        interactionHistory: [
          { type: 'choice', created_at: 1, text: '接受：前往会面' },
        ],
      },
    })

    expect(wrapper.text()).toContain('接受：前往会面')
    const buttons = wrapper.findAll('button.roleplay-dock__choice')
    expect(buttons).toHaveLength(2)
    expect(buttons[0].classes()).toContain('roleplay-dock__choice--accept')
    expect(buttons[1].classes()).toContain('roleplay-dock__choice--reject')

    await buttons[1].trigger('click')
    expect(wrapper.emitted('submit')?.[0]).toEqual(['reject'])
  })

  it('renders conversation view and emits send/end', async () => {
    const wrapper = mount(RoleplayConversationView, {
      props: {
        avatarName: '闻人雾',
        targetName: '阴长生',
        description: '世界已暂停，等待你继续发言。',
        caption: '玩家控制闻人雾发言，对方由 LLM 回复',
        modelValue: '',
        messages: [
          {
            id: 'm1',
            role: 'assistant',
            speaker_name: '阴长生',
            content: '阁下为何前来？',
            created_at: 1,
          },
        ],
        errorText: '',
        isSubmitting: false,
        submitText: '发送',
        interactionHistory: [
          { type: 'conversation_player', created_at: 1, text: '我来求一条路。' },
          { type: 'conversation_assistant', created_at: 2, text: '路未必在我手中。' },
        ],
      },
    })

    expect(wrapper.text()).toContain('闻人雾 ↔ 阴长生')
    expect(wrapper.text()).toContain('阁下为何前来？')
    expect(wrapper.text()).toContain('我来求一条路。')
    expect(wrapper.text()).toContain('路未必在我手中。')

    const textarea = wrapper.find('textarea.roleplay-dock__input--conversation')
    await textarea.setValue('我来求一条路。')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['我来求一条路。'])

    await wrapper.setProps({ modelValue: '我来求一条路。' })
    await wrapper.find('.roleplay-dock__conversation-actions .roleplay-dock__submit').trigger('click')
    expect(wrapper.emitted('send')).toHaveLength(1)

    await wrapper.find('button.roleplay-dock__submit--quiet').trigger('click')
    expect(wrapper.emitted('end')).toHaveLength(1)
  })

  it('renders idle hint', () => {
    const wrapper = mount(RoleplayIdleView)
    expect(wrapper.text()).toContain('当前仍在上帝视角观察世界')
  })

  it('limits interaction history to recent items', () => {
    const wrapper = mount(RoleplayInteractionHistory, {
      props: {
        maxItems: 2,
        items: [
          { type: 'command', created_at: 1, text: '第一条' },
          { type: 'command', created_at: 2, text: '第二条' },
          { type: 'command', created_at: 3, text: '第三条' },
        ],
      },
    })

    expect(wrapper.text()).not.toContain('第一条')
    expect(wrapper.text()).toContain('第二条')
    expect(wrapper.text()).toContain('第三条')
  })
})
