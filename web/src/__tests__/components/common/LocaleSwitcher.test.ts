import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { nextTick } from 'vue'

const mockSetLocale = vi.fn().mockResolvedValue(undefined)

vi.mock('@/stores/setting', () => ({
  useSettingStore: () => ({
    locale: 'zh-CN',
    setLocale: mockSetLocale,
  }),
}))

import LocaleSwitcher from '@/components/common/LocaleSwitcher.vue'
import { createTestI18n } from '@/__tests__/utils/i18n'

describe('LocaleSwitcher', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockSetLocale.mockClear()
    window.sessionStorage.clear()
  })

  it('renders splash trigger and opens locale panel', async () => {
    const wrapper = mount(LocaleSwitcher, {
      props: {
        variant: 'splash',
      },
      global: {
        plugins: [
          createPinia(),
          createTestI18n({
            ui: {
              language_switcher_button: 'Language',
              language_switcher_hint: 'Choose your display language',
            },
          }),
        ],
      },
    })

    expect(wrapper.find('.locale-trigger--splash').text()).toContain('Language')

    await wrapper.find('.locale-trigger--splash').trigger('click')

    expect(wrapper.find('.locale-panel').exists()).toBe(true)
    expect(wrapper.text()).toContain('English')
  })

  it('calls setLocale when selecting a locale', async () => {
    const wrapper = mount(LocaleSwitcher, {
      props: {
        variant: 'settings',
      },
      global: {
        plugins: [
          createPinia(),
          createTestI18n({
            ui: {
              language_switcher_button: 'Language',
              language_switcher_hint: 'Choose your display language',
            },
          }),
        ],
      },
    })

    await wrapper.find('.locale-trigger--settings').trigger('click')
    await wrapper.findAll('.locale-option')[2].trigger('click')
    await nextTick()

    expect(mockSetLocale).toHaveBeenCalledWith('en-US')
  })
})
