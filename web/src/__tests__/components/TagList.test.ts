import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'

// Mock getEntityColor.
const mockGetEntityColor = vi.fn()

vi.mock('@/utils/theme', () => ({
  getEntityColor: (entity: any) => mockGetEntityColor(entity),
}))

import TagList from '@/components/game/panels/info/components/TagList.vue'

describe('TagList', () => {
  const defaultTags = [
    { id: '1', name: 'Tag One' },
    { id: '2', name: 'Tag Two' },
    { id: '3', name: 'Tag Three' },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetEntityColor.mockReturnValue('#ff0000')
  })

  it('should render all tags', () => {
    const wrapper = mount(TagList, {
      props: {
        tags: defaultTags,
      },
    })

    const tags = wrapper.findAll('.tag')
    expect(tags.length).toBe(3)
    expect(tags[0].text()).toBe('Tag One')
    expect(tags[1].text()).toBe('Tag Two')
    expect(tags[2].text()).toBe('Tag Three')
  })

  it('should apply border color from getEntityColor', () => {
    mockGetEntityColor.mockImplementation((tag) => {
      if (tag.id === '1') return '#ff0000'
      if (tag.id === '2') return '#00ff00'
      return '#0000ff'
    })

    const wrapper = mount(TagList, {
      props: {
        tags: defaultTags,
      },
    })

    const tags = wrapper.findAll('.tag')

    expect(mockGetEntityColor).toHaveBeenCalledTimes(3)
    expect(tags[0].attributes('style')).toContain('border-color: rgb(255, 0, 0)')
    expect(tags[1].attributes('style')).toContain('border-color: rgb(0, 255, 0)')
    expect(tags[2].attributes('style')).toContain('border-color: rgb(0, 0, 255)')
  })

  it('should emit click with tag item when tag is clicked', async () => {
    const wrapper = mount(TagList, {
      props: {
        tags: defaultTags,
      },
    })

    const tags = wrapper.findAll('.tag')
    await tags[1].trigger('click')

    expect(wrapper.emitted('click')).toBeTruthy()
    expect(wrapper.emitted('click')?.length).toBe(1)
    expect(wrapper.emitted('click')?.[0]).toEqual([defaultTags[1]])
  })

  it('should emit click with correct tag on each click', async () => {
    const wrapper = mount(TagList, {
      props: {
        tags: defaultTags,
      },
    })

    const tags = wrapper.findAll('.tag')
    await tags[0].trigger('click')
    await tags[2].trigger('click')

    expect(wrapper.emitted('click')?.length).toBe(2)
    expect(wrapper.emitted('click')?.[0]).toEqual([defaultTags[0]])
    expect(wrapper.emitted('click')?.[1]).toEqual([defaultTags[2]])
  })

  it('should handle empty tags array', () => {
    const wrapper = mount(TagList, {
      props: {
        tags: [],
      },
    })

    const tags = wrapper.findAll('.tag')
    expect(tags.length).toBe(0)
    expect(wrapper.find('.tags-container').exists()).toBe(true)
  })

  it('should use tag name as key when id is not available', () => {
    const tagsWithoutId = [
      { name: 'No ID Tag 1' },
      { name: 'No ID Tag 2' },
    ]

    const wrapper = mount(TagList, {
      props: {
        tags: tagsWithoutId,
      },
    })

    const tags = wrapper.findAll('.tag')
    expect(tags.length).toBe(2)
    expect(tags[0].text()).toBe('No ID Tag 1')
    expect(tags[1].text()).toBe('No ID Tag 2')
  })

  it('should handle single tag', () => {
    const singleTag = [{ id: '1', name: 'Only Tag' }]

    const wrapper = mount(TagList, {
      props: {
        tags: singleTag,
      },
    })

    const tags = wrapper.findAll('.tag')
    expect(tags.length).toBe(1)
    expect(tags[0].text()).toBe('Only Tag')
  })

  it('should handle undefined color gracefully', () => {
    mockGetEntityColor.mockReturnValue(undefined)

    const wrapper = mount(TagList, {
      props: {
        tags: defaultTags,
      },
    })

    // Should not throw, tags should still render.
    const tags = wrapper.findAll('.tag')
    expect(tags.length).toBe(3)
  })

  it('should handle tags with additional properties', () => {
    const tagsWithExtra = [
      { id: '1', name: 'Tag', grade: 'SSR', rarity: 'epic' },
    ]

    const wrapper = mount(TagList, {
      props: {
        tags: tagsWithExtra,
      },
    })

    expect(wrapper.find('.tag').text()).toBe('Tag')
    expect(mockGetEntityColor).toHaveBeenCalledWith(tagsWithExtra[0])
  })
})
