import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import InfoPanelContainer from '@/components/game/panels/info/InfoPanelContainer.vue'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { useUiStore } from '@/stores/ui'

describe('InfoPanelContainer', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('should render successfully', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {}
    })

    const wrapper = mount(InfoPanelContainer, {
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          AvatarDetail: true,
          SectDetail: true,
          RegionDetail: true
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
  })

  it('should not close when pointerdown happens inside portrait panel', async () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {}
    })

    const wrapper = mount(InfoPanelContainer, {
      attachTo: document.body,
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          AvatarDetail: true,
          SectDetail: true,
          RegionDetail: true
        }
      }
    })

    const uiStore = useUiStore()
    uiStore.selectedTarget = { type: 'avatar', id: 'avatar-1' }
    uiStore.detailData = { id: 'avatar-1', name: 'Test Avatar' } as any
    await wrapper.vm.$nextTick()

    const closeSpy = vi.spyOn(uiStore, 'clearSelection')
    const portraitPanel = document.createElement('div')
    portraitPanel.className = 'portrait-panel'
    const inner = document.createElement('button')
    portraitPanel.appendChild(inner)
    document.body.appendChild(portraitPanel)

    Object.defineProperty(performance, 'now', {
      configurable: true,
      value: vi.fn(() => 1000),
    })

    inner.dispatchEvent(new Event('pointerdown', { bubbles: true }))
    await wrapper.vm.$nextTick()

    expect(closeSpy).not.toHaveBeenCalled()
  })

  it('should not render region subtitle in header', async () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {},
    })

    const wrapper = mount(InfoPanelContainer, {
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          AvatarDetail: true,
          SectDetail: true,
          RegionDetail: true,
        },
      },
    })

    const uiStore = useUiStore()
    uiStore.selectedTarget = { type: 'region', id: 'region-1' }
    uiStore.detailData = {
      id: 'region-1',
      name: '千机谷',
      type_name: '宗门驻地',
    } as any
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('千机谷')
    expect(wrapper.text()).not.toContain('宗门驻地')
    expect(wrapper.text()).not.toContain('固有地名')
  })
})
