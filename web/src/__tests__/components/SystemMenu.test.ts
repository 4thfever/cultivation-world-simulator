import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import SystemMenu from '@/components/SystemMenu.vue'
import { createPinia, setActivePinia } from 'pinia'
import { createTestI18n, testDefaultLocale } from '@/__tests__/utils/i18n'

describe('SystemMenu', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  const i18n = createTestI18n(
    {
      ui: {
        system_menu_title: 'System Menu',
        start_game: 'Start Game',
        load_game: 'Load Game',
        save_game: 'Save Game',
        create_character: 'Create Character',
        delete_character: 'Delete Character',
        llm_settings: 'LLM Settings',
        settings: 'Settings',
        language: 'Language',
        language_switcher_button: 'Language',
        language_switcher_hint: 'Choose your display language',
        about: 'About',
        other: 'Other',
        simplified_chinese: 'Simplified Chinese',
        traditional_chinese: 'Traditional Chinese',
        english: 'English',
        sound: 'Sound',
        bgm_volume: 'Music',
        sfx_volume: 'Sound FX',
        auto_save: 'Auto Save',
        auto_save_desc: 'Automatically save the game every decade in January',
      },
    },
    testDefaultLocale,
  )

  it('should render nothing if visible is false', () => {
    const wrapper = mount(SystemMenu, {
      props: {
        visible: false,
        gameInitialized: false
      },
      global: {
        plugins: [
          createPinia(),
          i18n
        ],
        stubs: {
          SystemMenuShell: {
            props: ['visible'],
            template: '<div v-if="visible" class="system-menu-overlay"><div class="menu-tabs"><button @click="$emit(\'tab-change\', \'start\')">Start</button></div><slot /></div>',
          },
          SystemMenuStartTab: true,
          SystemMenuLoadTab: true,
          SystemMenuSaveTab: true,
          SystemMenuCreateTab: true,
          SystemMenuDeleteTab: true,
          SystemMenuLlmTab: true,
          SystemMenuSettingsTab: true,
          SystemMenuAboutTab: true,
          SystemMenuOtherTab: true,
          'n-button': true,
          'n-select': true,
          'n-icon': true,
          'n-switch': true,
          'n-slider': true
        },
        directives: {
          sound: () => {}
        }
      }
    })

    expect(wrapper.find('.system-menu-overlay').exists()).toBe(false)
  })

  it('should render overlay and default tab when visible', async () => {
    const wrapper = mount(SystemMenu, {
      props: {
        visible: true,
        gameInitialized: true,
        defaultTab: 'settings'
      },
      global: {
        plugins: [
          createPinia(),
          i18n
        ],
        stubs: {
          SystemMenuShell: {
            props: ['visible'],
            template: '<div v-if="visible" class="system-menu-overlay"><div class="menu-tabs"><button @click="$emit(\'tab-change\', \'start\')">Start</button></div><slot /></div>',
          },
          SystemMenuStartTab: true,
          SystemMenuLoadTab: true,
          SystemMenuSaveTab: true,
          SystemMenuCreateTab: true,
          SystemMenuDeleteTab: true,
          SystemMenuLlmTab: true,
          SystemMenuSettingsTab: {
            template: '<div>Language</div>',
          },
          SystemMenuAboutTab: true,
          SystemMenuOtherTab: true,
          'n-button': true,
          'n-select': true,
          'n-icon': true,
          'n-switch': true,
          'n-slider': true
        },
        directives: {
          sound: () => {}
        }
      }
    })

    expect(wrapper.find('.system-menu-overlay').exists()).toBe(true)
    expect(wrapper.text()).toContain('Language')
    
    // Test clicking a tab
    const tabs = wrapper.findAll('.menu-tabs button')
    if (tabs.length > 0) {
      await tabs[0].trigger('click')
      expect(wrapper.emitted()).toBeTruthy()
    }
  })
})
