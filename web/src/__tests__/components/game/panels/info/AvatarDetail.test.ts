import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import AvatarDetail from '@/components/game/panels/info/AvatarDetail.vue'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

describe('AvatarDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  const i18n = createI18n({
    legacy: false,
    locale: 'zh-CN',
    messages: {
      'zh-CN': {
        game: {
          info_panel: {
            avatar: {
              set_objective: 'Set Objective',
              clear_objective: 'Clear Objective',
              stats: {
                realm: 'Realm',
                age: 'Age',
                origin: 'Origin',
                hp: 'HP',
                gender: 'Gender',
                alignment: 'Alignment',
                sect: 'Sect',
                root: 'Root',
                luck: 'Luck',
                magic_stone: 'Spirit Stone',
                appearance: 'Appearance',
                battle_strength: 'Battle Strength',
                emotion: 'Emotion',
              }
            }
          }
        },
        common: {
          none: 'None'
        }
      }
    }
  })

  const mockAvatarData = {
    id: 'avatar_1',
    name: 'Test Avatar',
    realm: 'Foundation',
    level: 1,
    age: 20,
    lifespan: 100,
    origin: 'Test Origin',
    hp: { cur: 100, max: 100 },
    gender: 'Male',
    alignment: 'Good',
    root: 'Gold',
    luck: 0,
    magic_stone: 0,
    appearance: 'Plain',
    base_battle_strength: 10,
    emotion: { emoji: '😀', name: 'Happy' },
    is_dead: false,
    current_effects: '',
    personas: [],
    materials: [],
    traits: [],
    items: [],
    skills: [],
    events: [],
    relations: [],
  }

  it('should render successfully', () => {
    const wrapper = mount(AvatarDetail, {
      props: {
        data: mockAvatarData as any
      },
      global: {
        plugins: [
          createPinia(),
          i18n
        ],
        stubs: {
          StatItem: true,
          EntityRow: true,
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
    // Check if the actions bar exists since it's not dead
    expect(wrapper.find('.actions-bar').exists()).toBe(true)
  })

  it('should display dead banner if avatar is dead', () => {
    const deadAvatar = { ...mockAvatarData, is_dead: true, death_info: { reason: 'Old age' } }
    const wrapper = mount(AvatarDetail, {
      props: {
        data: deadAvatar as any
      },
      global: {
        plugins: [
          createPinia(),
          i18n
        ],
        stubs: {
          StatItem: true,
          EntityRow: true,
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true
        }
      }
    })

    expect(wrapper.find('.dead-banner').exists()).toBe(true)
    expect(wrapper.find('.actions-bar').exists()).toBe(false)
  })

  it('renders identity and non-stranger attitude on separate lines', () => {
    const relationAvatar = {
      ...mockAvatarData,
      relations: [
        {
          target_id: 'avatar_2',
          name: '青岚',
          relation: '道侣 / 友好',
          relation_type: 'lovers',
          identity_relations: ['lovers'],
          numeric_relation: 'friend',
          friendliness: 12,
          realm: '金丹后期',
          sect: '凌霄剑宗',
        },
        {
          target_id: 'avatar_3',
          name: '丹七杀',
          relation: '陌生',
          relation_type: '',
          identity_relations: [],
          numeric_relation: 'stranger',
          friendliness: 0,
          realm: '金丹后期',
          sect: '金丹后期',
        },
      ],
    }

    const wrapper = mount(AvatarDetail, {
      props: {
        data: relationAvatar as any,
      },
      global: {
        plugins: [
          createPinia(),
          i18n,
        ],
        directives: {
          sound: () => {},
        },
        stubs: {
          StatItem: true,
          EntityRow: true,
          TagList: true,
          SecondaryPopup: true,
        },
      },
    })

    expect(wrapper.text()).toContain('道侣')
    expect(wrapper.text()).toContain('友好（12）')
    expect(wrapper.text()).not.toContain('态度：陌生')
    expect(wrapper.text()).not.toContain('身份：')
    expect(wrapper.text()).not.toContain('态度：')
    expect(wrapper.text()).not.toContain('丹七杀')
  })
})
