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
            tagline_en: 'Subtitle',
            subtitle_start_en: 'Start Game',
            subtitle_load_en: 'Load Game',
            subtitle_achievements_en: 'Achievements',
            subtitle_settings_en: 'Settings',
            subtitle_about_en: 'About',
            subtitle_exit_en: 'Exit',
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

  it('keeps splash subtitle and button sublabels in English for zh-CN', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {
        'zh-CN': {
          splash: {
            title: 'AI修仙世界模拟器',
            tagline_en: 'AI Cultivation World Simulator',
            subtitle_start_en: 'Start Game',
            subtitle_load_en: 'Load Game',
            subtitle_achievements_en: 'Achievements',
            subtitle_settings_en: 'Settings',
            subtitle_about_en: 'About',
            subtitle_exit_en: 'Exit',
          },
          ui: {
            start_game: '开始游戏',
            load_game: '加载游戏',
            achievements: '成就',
            settings: '设置',
            about: '关于',
            exit: '离开',
            language_switcher_button: 'Language',
            language_switcher_hint: '选择界面语言',
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

    expect(wrapper.find('.title-area p').text()).toBe('AI Cultivation World Simulator')
    const subLabels = wrapper.findAll('.btn-sub').map((node) => node.text())
    expect(subLabels).toEqual([
      'Start Game',
      'Load Game',
      'Achievements',
      'Settings',
      'About',
      'Exit',
    ])
  })
})
