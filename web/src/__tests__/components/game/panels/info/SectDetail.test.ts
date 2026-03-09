import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach } from 'vitest'
import SectDetail from '@/components/game/panels/info/SectDetail.vue'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

describe('SectDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render successfully', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {}
    })

    const wrapper = mount(SectDetail, {
      props: {
        data: {
          id: '1',
          name: 'Test Sect',
          alignment: 'Good',
          member_count: 10,
          desc: 'Test'
        } as any
      },
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          StatItem: true,
          EntityRow: true,
          TagList: true
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
  })

  it('displays influence_radius, magic_stone, total_battle_strength in stats', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {}
    })

    const data = {
      id: '1',
      name: 'Test Sect',
      alignment: 'Good',
      desc: 'Intro',
      style: '剑修',
      hq_name: 'HQ',
      hq_desc: 'HQ desc',
      effect_desc: 'Effect',
      preferred_weapon: '剑',
      members: [],
      orthodoxy: null,
      techniques: [],
      magic_stone: 100,
      is_active: true,
      total_battle_strength: 2500.7,
      influence_radius: 3,
      color: '#ff0000',
    }

    const wrapper = mount(SectDetail, {
      props: { data },
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          SecondaryPopup: true,
          StatItem: false,
          EntityRow: true,
          RelationRow: true,
          TagList: true,
        }
      }
    })

    const text = wrapper.text()
    expect(text).toContain('100')   // magic_stone
    expect(text).toContain('2500')  // total_battle_strength (floored)
    expect(text).toContain('3')     // influence_radius
  })
})
