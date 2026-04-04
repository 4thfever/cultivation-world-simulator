import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import MapLayer from '@/components/game/MapLayer.vue'
import { createPinia, setActivePinia } from 'pinia'
import { createTestI18n } from '@/__tests__/utils/i18n'

describe('MapLayer', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render successfully', () => {
    const i18n = createTestI18n({}, 'en-US')
    const wrapper = mount(MapLayer, {
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          container: true,
          sprite: true,
          graphics: true
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
  })
})
