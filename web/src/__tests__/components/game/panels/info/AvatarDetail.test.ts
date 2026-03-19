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
})
