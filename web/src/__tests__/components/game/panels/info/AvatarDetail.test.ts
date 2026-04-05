import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { defineComponent, h } from 'vue'
import AvatarDetail from '@/components/game/panels/info/AvatarDetail.vue'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

const entityRowSpy = vi.fn()

vi.mock('@/components/game/panels/info/components/EntityRow.vue', () => ({
  default: defineComponent({
    name: 'EntityRow',
    props: ['item', 'meta', 'compact', 'detailsBelow'],
    emits: ['click'],
    setup(props) {
      entityRowSpy(props)
      return () => h('div', { class: 'entity-row-stub' }, props.item?.name || '')
    },
  }),
}))

describe('AvatarDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    entityRowSpy.mockClear()
  })

  const i18n = createI18n({
    legacy: false,
    locale: 'zh-CN',
    messages: {
      'zh-CN': {
        game: {
          info_panel: {
            avatar: {
              empty_short: '-',
              set_objective: 'Set Objective',
              clear_objective: 'Clear Objective',
              long_term_objective: 'Long-term Objective',
              short_term_objective: 'Short-term Objective',
              portrait: {
                entry: 'Change Portrait',
                preview_alt: 'Portrait Preview',
              },
              dead_with_reason: 'Dead ({reason})',
              stats: {
                realm: 'Realm',
                age: 'Age',
                origin: 'Origin',
                hp: 'HP',
                gender: 'Gender',
                alignment: 'Alignment',
                sect: 'Sect',
                rogue: 'Rogue',
                official_rank: 'Official Rank',
                sect_contribution: 'Sect Contribution',
                root: 'Root',
                luck: 'Luck',
                magic_stone: 'Spirit Stone',
                appearance: 'Appearance',
                battle_strength: 'Battle Strength',
                emotion: 'Emotion',
              },
              sections: {
                traits: 'Traits',
                techniques_equipment: 'Arts & Gear',
                goldfinger: 'Goldfinger',
                relations: 'Relations',
                current_effects: 'Current Effects',
              },
              adjust: {
                entry: 'Adjust',
                empty_item: 'No {label}',
                categories: {
                  personas: 'Traits',
                  technique: 'Technique',
                  weapon: 'Weapon',
                  auxiliary: 'Auxiliary',
                  goldfinger: 'Goldfinger',
                },
              },
              father_short: 'Father',
              mother_short: 'Mother',
              mortal_realm: 'Mortal',
            }
          }
        },
        common: {
          none: 'None'
        },
        ui: {
          create_avatar: {
            gender_labels: {
              male: 'Male',
              female: 'Female',
            },
          },
          other: 'Other',
        },
      }
    }
  })

  const mockAvatarData = {
    id: 'avatar_1',
    name: 'Test Avatar',
    realm: 'Foundation',
    pic_id: 7,
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
    goldfinger: undefined,
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
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
    // Check if the actions bar exists since it's not dead
    expect(wrapper.find('.actions-bar').exists()).toBe(true)
    expect(wrapper.find('.avatar-header').exists()).toBe(true)
    expect(wrapper.find('.portrait-button').exists()).toBe(true)
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
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
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
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
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

  it('renders long effect sources as separate rows with segmented content', () => {
    const effectAvatar = {
      ...mockAvatarData,
      current_effects: '[Orthodoxy [Nature]] Special Ability Respiration Refinement Success Rate +15.0%; Battle Strength +20\n[Heaven and Earth Phenomenon] Respiration Experience +20',
    }

    const wrapper = mount(AvatarDetail, {
      props: {
        data: effectAvatar as any,
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
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        },
      },
    })

    const rows = wrapper.findAll('.effect-row')
    expect(rows).toHaveLength(2)
    expect(rows[0].find('.effect-source').text()).toBe('Orthodoxy [Nature]')
    expect(rows[0].find('.effect-content').text()).toContain('Special Ability Respiration Refinement Success Rate +15.0%')
    expect(rows[0].find('.effect-content').text()).toContain('Battle Strength +20')
    expect(rows[1].find('.effect-source').text()).toBe('Heaven and Earth Phenomenon')
  })

  it('renders goldfinger entry when present', () => {
    const wrapper = mount(AvatarDetail, {
      props: {
        data: {
          ...mockAvatarData,
          goldfinger: {
            id: '1',
            name: '气运之子',
            desc: '天命眷顾',
            effect_desc: '气运 +20',
          },
        } as any,
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
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Goldfinger')
    expect(wrapper.findAll('.equipment-slot-block')).toHaveLength(4)
    expect(wrapper.text()).toContain('天命眷顾')
    expect(entityRowSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        item: expect.objectContaining({
          name: '气运之子',
          desc: '天命眷顾',
        }),
      }),
    )
  })

  it('passes goldfinger category and current item into adjust panel when clicking edit', async () => {
    let capturedProps: Record<string, unknown> | null = null
    const AvatarAdjustPanelStub = defineComponent({
      name: 'AvatarAdjustPanel',
      props: ['avatarId', 'category', 'currentItem', 'currentPersonas'],
      setup(props) {
        capturedProps = props as unknown as Record<string, unknown>
        return () => h('div', { class: 'adjust-panel-stub' })
      },
    })

    const wrapper = mount(AvatarDetail, {
      props: {
        data: {
          ...mockAvatarData,
          goldfinger: {
            id: '1',
            name: '气运之子',
            desc: '天命眷顾',
            effect_desc: '气运 +20',
          },
        } as any,
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
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: AvatarAdjustPanelStub,
          AvatarPortraitPanel: true,
        },
      },
    })

    const adjustButtons = wrapper.findAll('button.adjust-btn.inline')
    expect(adjustButtons).toHaveLength(4)

    await adjustButtons[3].trigger('click')

    expect(capturedProps).not.toBeNull()
    expect(capturedProps?.category).toBe('goldfinger')
    expect(capturedProps?.currentItem).toMatchObject({
      id: '1',
      name: '气运之子',
    })
  })
})
