import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach } from 'vitest'
import RegionDetail from '@/components/game/panels/info/RegionDetail.vue'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

describe('RegionDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render successfully', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {
        'zh-CN': {
          game: {
            population: '人口',
            mortal_system: {
              population_ratio_value: '{current} / {capacity} 万',
            },
            info_panel: {
              region: {
                type_explanations: {
                  city: '城市说明',
                  ruin: '遗迹说明',
                  cave: '洞府说明',
                  sect: '宗门说明',
                  normal: '普通区域说明',
                },
              },
            },
          },
        },
      },
    })

    const wrapper = mount(RegionDetail, {
      props: {
        data: {
          id: '1',
          name: 'Test City',
          type: 'city',
          type_name: 'Test',
          desc: 'Test Desc',
          animals: [],
          plants: [],
          lodes: [],
          population: 120,
          population_capacity: 200,
        }
      },
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          EntityRow: true,
          RelationRow: true,
          SecondaryPopup: true,
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
    expect(wrapper.text()).toContain('人口')
    expect(wrapper.text()).toContain('120.0 / 200.0 万')
  })
})
