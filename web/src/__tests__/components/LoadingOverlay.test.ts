import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach } from 'vitest'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

describe('LoadingOverlay', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render successfully', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {
        'zh-CN': {
          loading: {
            title: 'Loading',
            subtitle: 'Subtitle',
            phase: {
              chaos: 'Chaos',
            },
            tips_label: 'Tips',
            elapsed: 'Elapsed {seconds}s',
            tips: [],
            unknown_error: 'Unknown error',
            error: 'Error',
            retry: 'Retry',
          },
          common: {
            version: 'Version',
          }
        }
      }
    })

    const wrapper = mount(LoadingOverlay, {
      props: {
        status: null,
      },
      global: {
        plugins: [createPinia(), i18n],
      }
    })

    expect(wrapper.exists()).toBe(true)
  })
})
