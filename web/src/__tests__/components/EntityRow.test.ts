import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'

// Mock getEntityColor.
const mockGetEntityColor = vi.fn()

vi.mock('@/utils/theme', () => ({
  getEntityColor: (entity: any) => mockGetEntityColor(entity),
}))

import EntityRow from '@/components/game/panels/info/components/EntityRow.vue'

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
    })

    expect(wrapper.find('.name').text()).toBe('Test Entity')
  })

  it('should apply color from getEntityColor', () => {
    mockGetEntityColor.mockReturnValue('#00ff00')

    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
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
    })

    expect(wrapper.find('.meta').exists()).toBe(true)
    expect(wrapper.find('.meta').text()).toBe('Proficiency 50%')
  })

  it('should hide meta when not provided', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
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
    })

    expect(wrapper.find('.grade').exists()).toBe(true)
    expect(wrapper.find('.grade').text()).toBe('SSR')
  })

  it('should hide grade when item has no grade', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
    })

    expect(wrapper.find('.grade').exists()).toBe(false)
  })

  it('should have compact class when compact is true', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
        compact: true,
      },
    })

    expect(wrapper.find('.entity-row').classes()).toContain('compact')
  })

  it('should not have compact class when compact is false', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
        compact: false,
      },
    })

    expect(wrapper.find('.entity-row').classes()).not.toContain('compact')
  })

  it('should not have compact class when compact not provided', () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
    })

    expect(wrapper.find('.entity-row').classes()).not.toContain('compact')
  })

  it('should emit click on click', async () => {
    const wrapper = mount(EntityRow, {
      props: {
        item: defaultItem,
      },
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
    })

    // Should not throw, just render without color.
    expect(wrapper.find('.name').exists()).toBe(true)
  })
})
