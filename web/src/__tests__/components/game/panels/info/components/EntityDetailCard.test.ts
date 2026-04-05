import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { createI18n } from 'vue-i18n'
import EntityDetailCard from '@/components/game/panels/info/components/EntityDetailCard.vue'

function buildI18n() {
  return createI18n({
    legacy: false,
    locale: 'zh-CN',
    messages: {
      'zh-CN': {
        game: {
          info_panel: {
            popup: {
              effect: '效果',
              drops: '掉落',
              hq: '总部',
            },
          },
        },
        technique_grades: {
          UPPER: '上品',
        },
      },
    },
  })
}

describe('EntityDetailCard', () => {
  it('renders epic badge style for rarity-driven entities like goldfingers', () => {
    const wrapper = mount(EntityDetailCard, {
      props: {
        item: {
          id: '1',
          name: '穿越者',
          desc: '现代思维仍在影响修仙视角',
          rarity: 'SR',
        } as any,
      },
      global: {
        plugins: [buildI18n()],
      },
    })

    const badge = wrapper.find('.grade-badge')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('SR')
    expect(badge.classes()).toContain('grade-epic')
  })

  it('renders description from desc', () => {
    const wrapper = mount(EntityDetailCard, {
      props: {
        item: {
          id: '3',
          name: '气运之子',
          rarity: 'SSR',
          desc: '你仿佛生来便被天地眷顾，很多人求而不得的机缘总会向你靠近。',
        } as any,
      },
      global: {
        plugins: [buildI18n()],
      },
    })

    expect(wrapper.text()).toContain('你仿佛生来便被天地眷顾')
  })

  it('renders legendary badge style for SSR entities', () => {
    const wrapper = mount(EntityDetailCard, {
      props: {
        item: {
          id: '2',
          name: '气运之子',
          desc: '天命偏爱，机缘主动靠近',
          rarity: 'SSR',
        } as any,
      },
      global: {
        plugins: [buildI18n()],
      },
    })

    const badge = wrapper.find('.grade-badge')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('SSR')
    expect(badge.classes()).toContain('grade-legendary')
  })
})
