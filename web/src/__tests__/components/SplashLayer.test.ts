import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import SplashLayer from '@/components/SplashLayer.vue'
import { createI18n } from 'vue-i18n'

vi.mock('@/composables/useBgm', () => ({
  useBgm: () => ({
    play: vi.fn(),
  }),
}))

describe('SplashLayer', () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it('should render successfully', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {
        'zh-CN': {
          splash: {
            title: 'Title',
            subtitle: 'Subtitle',
            click_to_start: 'Click to start'
          },
          ui: {
            start_game: 'Start',
            load_game: 'Load',
            achievements: 'Achievements',
            settings: 'Settings',
            about: 'About',
            exit: 'Exit',
            language_switcher_button: 'Language',
            language_switcher_hint: 'Choose your display language',
          }
        }
      }
    })

    const wrapper = mount(SplashLayer, {
      global: {
        plugins: [i18n],
        directives: {
          sound: () => {},
        },
      }
    })

    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.splash-container').exists()).toBe(true)
    expect(wrapper.find('.locale-trigger--splash').exists()).toBe(true)
  })
})
