import { mount } from '@vue/test-utils'
import { reactive, nextTick } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createI18n } from 'vue-i18n'

import RoleplayPanel from '@/components/game/panels/info/components/RoleplayPanel.vue'

const roleplayStoreMock = reactive({
  session: {
    controlled_avatar_id: null as string | null,
    status: 'inactive',
    pending_request: null,
    last_prompt_context: null as Record<string, unknown> | null,
  },
  isSubmitting: false,
  fetchSession: vi.fn(async () => roleplayStoreMock.session),
  startRoleplay: vi.fn(async () => roleplayStoreMock.session),
  stopRoleplay: vi.fn(async () => roleplayStoreMock.session),
})

vi.mock('@/stores/roleplay', () => ({
  useRoleplayStore: () => roleplayStoreMock,
}))

const uiStoreMock = {
  select: vi.fn(),
}

vi.mock('@/stores/ui', () => ({
  useUiStore: () => uiStoreMock,
}))

function createRoleplayI18n() {
  return createI18n({
    legacy: false,
    locale: 'zh',
    messages: {
      zh: {
        game: {
          roleplay: {
            panel: {
              start: '扮演',
              stop: '退出扮演',
              controlled_by: '当前正在扮演：{avatar}',
              go_to_controlled: '前往该角色',
            },
            fallback: {
              avatar_name: '角色',
            },
          },
        },
      },
    },
  })
}

describe('RoleplayPanel', () => {
  beforeEach(() => {
    roleplayStoreMock.session.controlled_avatar_id = null
    roleplayStoreMock.session.status = 'inactive'
    roleplayStoreMock.session.last_prompt_context = null
    roleplayStoreMock.isSubmitting = false
    roleplayStoreMock.fetchSession.mockClear()
    roleplayStoreMock.startRoleplay.mockClear()
    roleplayStoreMock.stopRoleplay.mockClear()
    uiStoreMock.select.mockClear()
  })

  it('shows start button and starts roleplay for current avatar', async () => {
    const wrapper = mount(RoleplayPanel, {
      global: { plugins: [createRoleplayI18n()] },
      props: {
        avatar: { id: 'avatar-1' },
      },
    })
    await nextTick()

    const button = wrapper.get('button.roleplay-btn')
    expect(button.text()).toBe('扮演')

    await button.trigger('click')
    expect(roleplayStoreMock.startRoleplay).toHaveBeenCalledWith('avatar-1')
  })

  it('fetches roleplay session only once on initial mount', async () => {
    mount(RoleplayPanel, {
      global: { plugins: [createRoleplayI18n()] },
      props: {
        avatar: { id: 'avatar-1' },
      },
    })
    await nextTick()

    expect(roleplayStoreMock.fetchSession).toHaveBeenCalledTimes(1)
  })

  it('shows stop button when current avatar is controlled', async () => {
    roleplayStoreMock.session.controlled_avatar_id = 'avatar-1'

    const wrapper = mount(RoleplayPanel, {
      global: { plugins: [createRoleplayI18n()] },
      props: {
        avatar: { id: 'avatar-1' },
      },
    })
    await nextTick()

    const button = wrapper.get('button.roleplay-btn')
    expect(button.text()).toBe('退出扮演')

    await button.trigger('click')
    expect(roleplayStoreMock.stopRoleplay).toHaveBeenCalledWith('avatar-1')
  })

  it('disables start button when another avatar is already controlled', async () => {
    roleplayStoreMock.session.controlled_avatar_id = 'avatar-2'
    roleplayStoreMock.session.last_prompt_context = { avatar_name: '冷清雅' }

    const wrapper = mount(RoleplayPanel, {
      global: { plugins: [createRoleplayI18n()] },
      props: {
        avatar: { id: 'avatar-1' },
      },
    })
    await nextTick()

    const button = wrapper.get('button.roleplay-btn')
    expect(button.text()).toBe('扮演')
    expect(button.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('当前正在扮演：冷清雅')

    await wrapper.get('button.roleplay-btn--ghost').trigger('click')
    expect(uiStoreMock.select).toHaveBeenCalledWith('avatar', 'avatar-2')
  })
})
