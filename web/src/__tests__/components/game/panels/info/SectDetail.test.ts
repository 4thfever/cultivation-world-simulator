import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import SectDetail from '@/components/game/panels/info/SectDetail.vue'

function createTestI18n() {
  return createI18n({
    legacy: false,
    locale: 'en-US',
    messages: {
      'en-US': {
        common: {
          none: 'None',
        },
        game: {
          sect_relations: {
            status_war: 'War',
            status_peace: 'Peace',
            duration_months: '{count} months',
          },
          info_panel: {
            sect: {
              stats: {
                alignment: 'Alignment',
                orthodoxy: 'Orthodoxy',
                style: 'Style',
                preferred: 'Preferred Weapon',
                members: 'Members',
                total_battle_strength: 'Total Battle Strength',
                influence_radius: 'Influence Radius',
                magic_stone: 'Magic Stone',
              },
              sections: {
                intro: 'Intro',
                hq: 'HQ - {name}',
                bonus: 'Bonus',
                diplomacy: 'Diplomacy',
                thinking: 'Sect Thinking',
                techniques: 'Techniques',
                members: 'Members',
              },
              no_bonus: 'No bonus',
              no_runtime_effect: 'No active runtime effect',
              runtime_effect_meta: '{source} remains for {months} months',
              runtime_effect_meta_permanent: '{source} is permanent',
            },
          },
        },
      },
    },
  })
}

describe('SectDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render successfully', () => {
    const i18n = createTestI18n()
    const wrapper = mount(SectDetail, {
      props: {
        data: {
          id: '1',
          name: 'Test Sect',
          alignment: 'Good',
          member_count: 10,
          desc: 'Test',
          style: 'Sword',
          preferred_weapon: 'Sword',
          members: [],
          orthodoxy: null,
          techniques: [],
          hq_name: 'HQ',
          hq_desc: 'HQ desc',
          effect_desc: '',
          total_battle_strength: 0,
          influence_radius: 0,
          magic_stone: 0,
          runtime_effect_items: [],
          diplomacy_items: [],
          yearly_thinking: '',
        } as any,
      },
      global: {
        plugins: [createPinia(), i18n],
        directives: {
          sound: () => {},
        },
        stubs: {
          StatItem: true,
          EntityRow: true,
          TagList: true,
        },
      },
    })

    expect(wrapper.exists()).toBe(true)
  })

  it('displays stats and runtime sect effects', () => {
    const i18n = createTestI18n()
    const data = {
      id: '1',
      name: 'Test Sect',
      alignment: 'Good',
      desc: 'Intro',
      style: 'Sword',
      hq_name: 'HQ',
      hq_desc: 'HQ desc',
      effect_desc: 'Sect bonus',
      preferred_weapon: 'Sword',
      members: [],
      orthodoxy: null,
      techniques: [],
      magic_stone: 100,
      is_active: true,
      total_battle_strength: 2500.7,
      influence_radius: 3,
      color: '#ff0000',
      runtime_effect_items: [
        {
          source: 'sect_random_event',
          source_label: 'Sect random event',
          desc: 'Extra income per tile +0.8',
          remaining_months: 60,
          is_permanent: false,
        },
      ],
      diplomacy_items: [
        {
          other_sect_id: 2,
          other_sect_name: 'Enemy Sect',
          status: 'war',
          duration_months: 18,
          war_months: 18,
          peace_months: 0,
        },
      ],
      yearly_thinking: '我宗观天下势力分化加剧，当先稳住边界与资源脉络，再图联盟突破，以争中局主动。',
    }

    const wrapper = mount(SectDetail, {
      props: { data },
      global: {
        plugins: [createPinia(), i18n],
        directives: {
          sound: () => {},
        },
        stubs: {
          SecondaryPopup: true,
          StatItem: false,
          EntityRow: true,
          RelationRow: false,
          TagList: true,
        },
      },
    })

    const text = wrapper.text()
    expect(text).toContain('100')
    expect(text).toContain('2500')
    expect(text).toContain('3')
    expect(text).toContain('Extra income per tile +0.8')
    expect(text).toContain('Sect random event remains for 60 months')
    expect(text).toContain('Enemy Sect')
    expect(text).toContain('我宗观天下势力分化加剧')
  })
})
