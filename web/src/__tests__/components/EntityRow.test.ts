import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestI18n } from '@/__tests__/utils/i18n'

// Mock getEntityColor.
const mockGetEntityColor = vi.fn()

vi.mock('@/utils/theme', () => ({
  getEntityColor: (entity: any) => mockGetEntityColor(entity),
  getEntityGradeTone: (grade?: string | null) => {
    const value = String(grade || '').toUpperCase()
    if (value.includes('SSR') || value.includes('ARTIFACT') || value.includes('法宝')) return 'legendary'
    if (value.includes('SR') || value.includes('UPPER') || value.includes('上品') || value.includes('宝物')) return 'epic'
    return 'default'
  },
}))

import EntityRow from '@/components/game/panels/info/components/EntityRow.vue'

const i18n = createTestI18n({
  technique_grades: {
    LOWER: 'LOWER',
    MIDDLE: 'MIDDLE',
    UPPER: 'UPPER',
  },
  realms: {},
  game: {
    ranking: {
      stages: {
        early: 'early',
        middle: 'middle',
        late: 'late',
      },
    },
  },
})

const globalConfig = {
  global: {
    directives: {
      sound: () => {},
    },
    plugins: [i18n],
  },
}

describe('EntityRow', () => {
  const defaultItem = {
    id: '1',
    name: 'Test Entity',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetEntityColor.mockReturnValue('#ff0000')
  })

  it('should render item name', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
      ...globalConfig,
    })

    expect(wrapper.find('.name').text()).toBe('Test Entity')
  })

  it('should apply color from getEntityColor', () => {
    mockGetEntityColor.mockReturnValue('#00ff00')

    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
      ...globalConfig,
    })

    expect(mockGetEntityColor).toHaveBeenCalledWith(defaultItem)
    expect(wrapper.find('.name').attributes('style')).toContain('color: rgb(0, 255, 0)')
  })

  it('should render meta when provided', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
        meta: 'Proficiency 50%',
      },
      ...globalConfig,
    })

    expect(wrapper.find('.meta').exists()).toBe(true)
    expect(wrapper.find('.meta').text()).toBe('Proficiency 50%')
  })

  it('should hide meta when not provided', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
      ...globalConfig,
    })

    expect(wrapper.find('.meta').exists()).toBe(false)
  })

  it('should render grade when item has grade', () => {
    const itemWithGrade = {
      ...defaultItem,
      grade: 'SSR',
    }

    const wrapper = mount(EntityRow, {
      props: {
        item: itemWithGrade,
      },
      ...globalConfig,
    })

    expect(wrapper.find('.grade').exists()).toBe(true)
    expect(wrapper.find('.grade').text()).toBe('SSR')
    expect(wrapper.find('.grade').classes()).toContain('grade-legendary')
  })

  it('should render rarity when item has rarity but no grade', () => {
    const itemWithRarity = {
      ...defaultItem,
      rarity: 'SR',
    }

    const wrapper = mount(EntityRow, {
      props: {
        item: itemWithRarity,
      },
      ...globalConfig,
    })

    expect(wrapper.find('.grade').exists()).toBe(true)
    expect(wrapper.find('.grade').text()).toBe('SR')
    expect(wrapper.find('.grade').classes()).toContain('grade-epic')
  })

  it('should hide grade when item has no grade', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
      ...globalConfig,
    })

    expect(wrapper.find('.grade').exists()).toBe(false)
  })

  it('should have compact class when compact is true', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
        compact: true,
      },
      ...globalConfig,
    })

    expect(wrapper.find('.entity-row').classes()).toContain('compact')
  })

  it('should render stacked details layout when detailsBelow is true', () => {
    const itemWithGrade = {
      ...defaultItem,
      grade: 'SR',
    }

    const wrapper = mount(EntityRow, {
      props: {
        item: itemWithGrade,
        meta: 'Proficiency 50%',
        detailsBelow: true,
      },
      ...globalConfig,
    })

    expect(wrapper.find('.entity-row').classes()).toContain('details-below')
    expect(wrapper.find('.entity-row').classes()).toContain('details-inline-preferred')
    expect(wrapper.find('.details-line').exists()).toBe(false)
    expect(wrapper.find('.inline-info').exists()).toBe(true)
    expect(wrapper.find('.meta').text()).toBe('Proficiency 50%')
    expect(wrapper.find('.grade').text()).toBe('SR')
  })

  it('should render stacked details line for locales that prefer stacked details', () => {
    const itemWithGrade = {
      ...defaultItem,
      grade: 'SR',
    }

    const wrapper = mount(EntityRow, {
      props: {
        item: itemWithGrade,
        meta: 'Proficiency 50%',
        detailsBelow: true,
      },
      global: {
        directives: {
          sound: () => {},
        },
        plugins: [createTestI18n({
          technique_grades: {
            LOWER: 'LOWER',
            MIDDLE: 'MIDDLE',
            UPPER: 'UPPER',
          },
          realms: {},
          game: {
            ranking: {
              stages: {
                early: 'early',
                middle: 'middle',
                late: 'late',
              },
            },
          },
        }, 'en-US')],
      },
    })

    expect(wrapper.find('.entity-row').classes()).toContain('details-below')
    expect(wrapper.find('.entity-row').classes()).toContain('details-stacked')
    expect(wrapper.find('.details-line').exists()).toBe(true)
    expect(wrapper.find('.inline-info').exists()).toBe(false)
    expect(wrapper.find('.meta').text()).toBe('Proficiency 50%')
    expect(wrapper.find('.grade').text()).toBe('SR')
  })

  it('should not have compact class when compact is false', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
        compact: false,
      },
      ...globalConfig,
    })

    expect(wrapper.find('.entity-row').classes()).not.toContain('compact')
  })

  it('should not have compact class when compact not provided', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
      ...globalConfig,
    })

    expect(wrapper.find('.entity-row').classes()).not.toContain('compact')
  })

  it('should emit click on click', async () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
      ...globalConfig,
    })

    await wrapper.find('.entity-row').trigger('click')

    expect(wrapper.emitted('click')).toBeTruthy()
    expect(wrapper.emitted('click')?.length).toBe(1)
  })

  it('should render all props together', () => {
    mockGetEntityColor.mockReturnValue('#0000ff')

    const itemWithGrade = {
      id: '2',
      name: 'Full Entity',
      grade: 'SR',
    }

    const wrapper = mount(EntityRow, {
      props: {
        item: itemWithGrade,
        meta: 'Meta Info',
        compact: true,
      },
      ...globalConfig,
    })

    expect(wrapper.find('.name').text()).toBe('Full Entity')
    expect(wrapper.find('.meta').text()).toBe('Meta Info')
    expect(wrapper.find('.grade').text()).toBe('SR')
    expect(wrapper.find('.entity-row').classes()).toContain('compact')
  })

  it('should handle undefined color from getEntityColor', () => {
    mockGetEntityColor.mockReturnValue(undefined)

    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
      ...globalConfig,
    })

    // Should not throw, just render without color.
    expect(wrapper.find('.name').exists()).toBe(true)
  })
})
