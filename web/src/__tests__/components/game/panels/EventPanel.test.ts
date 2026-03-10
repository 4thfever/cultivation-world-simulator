import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import EventPanel from '@/components/game/panels/EventPanel.vue'
import { createI18n } from 'vue-i18n'
import { reactive } from 'vue'
import { NSelect } from 'naive-ui'

const avatarStoreMock = reactive({
  avatarList: [
    { id: 'a1', name: 'Alice', is_dead: false },
  ],
})

const eventStoreMock = reactive({
  events: [],
  eventsHasMore: false,
  eventsLoading: false,
  resetEvents: vi.fn(async () => {}),
  loadMoreEvents: vi.fn(async () => {}),
})

const uiStoreMock = {
  select: vi.fn(),
}

const mapStoreMock = reactive({
  regions: new Map<string | number, { id: string; name: string; type: string; sect_id?: number; sect_name?: string; sect_color?: string; x: number; y: number }>(),
})

vi.mock('@/stores/avatar', () => ({
  useAvatarStore: () => avatarStoreMock,
}))

vi.mock('@/stores/event', () => ({
  useEventStore: () => eventStoreMock,
}))

vi.mock('@/stores/ui', () => ({
  useUiStore: () => uiStoreMock,
}))

vi.mock('@/stores/map', () => ({
  useMapStore: () => mapStoreMock,
}))

describe('EventPanel', () => {
  beforeEach(() => {
    eventStoreMock.events = []
    eventStoreMock.eventsHasMore = false
    eventStoreMock.eventsLoading = false
    eventStoreMock.resetEvents.mockClear()
    eventStoreMock.loadMoreEvents.mockClear()
    uiStoreMock.select.mockClear()
    mapStoreMock.regions = new Map([
      ['r1', { id: 'r1', name: '明心山', type: 'sect', sect_id: 1, sect_name: '青云门', sect_color: '#4DD0E1', x: 10, y: 10 }],
      ['r2', { id: 'r2', name: '赤焰峰', type: 'sect', sect_id: 2, sect_name: '天火宗', sect_color: '#8D6E63', x: 20, y: 20 }],
    ])
  })

  it('should render successfully', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh',
      messages: {
        zh: {
          game: {
            event_panel: {
              title: 'Events',
              filter_all: 'All',
              deceased: '(dead)',
              add_second: '+1',
              load_more: 'load',
              empty_none: 'none',
              empty_single: 'none',
              empty_dual: 'none',
            }
          },
          common: { loading: 'loading', year: '年', month: '月' },
        }
      }
    })

    const wrapper = mount(EventPanel, {
      global: {
        plugins: [i18n],
        directives: {
          sound: () => {}
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
  })

  it('should render event content as text, not raw html', async () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh',
      messages: {
        zh: {
          game: { event_panel: { title: 'Events', filter_all: 'All', deceased: '(dead)', add_second: '+1', load_more: 'load', empty_none: 'none', empty_single: 'none', empty_dual: 'none' } },
          common: { loading: 'loading', year: '年', month: '月' },
        },
      },
    })

    eventStoreMock.events = [
      {
        id: 'e1',
        text: '',
        content: '<img src=x onerror=alert(1)> Alice',
        year: 1,
        month: 1,
        timestamp: 13,
        relatedAvatarIds: ['a1'],
        isMajor: false,
        isStory: false,
      },
    ]

    const wrapper = mount(EventPanel, {
      global: {
        plugins: [i18n],
      },
    })

    const html = wrapper.html()
    expect(html).not.toContain('<img')
    expect(html).toContain('&lt;img src=x onerror=alert(1)&gt;')
    expect(wrapper.find('.clickable-avatar').text()).toBe('Alice')
  })

  it('should render clickable sect name with fixed color and jump to sect panel', async () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh',
      messages: {
        zh: {
          game: { event_panel: { title: 'Events', filter_all: 'All', deceased: '(dead)', add_second: '+1', load_more: 'load', empty_none: 'none', empty_single: 'none', empty_dual: 'none' } },
          common: { loading: 'loading', year: '年', month: '月' },
        },
      },
    })

    eventStoreMock.events = [
      {
        id: 'e2',
        text: '',
        content: 'Alice joined 青云门',
        year: 1,
        month: 2,
        timestamp: 14,
        relatedAvatarIds: ['a1'],
        relatedSects: [1],
        isMajor: false,
        isStory: false,
      },
    ]

    const wrapper = mount(EventPanel, {
      global: { plugins: [i18n] },
    })

    const sectNode = wrapper.find('.clickable-sect')
    expect(sectNode.exists()).toBe(true)
    expect(sectNode.text()).toBe('青云门')
    expect(sectNode.attributes('style')).toContain('rgb(77, 208, 225)')

    await sectNode.trigger('click')
    expect(uiStoreMock.select).toHaveBeenCalledWith('sect', '1')
  })

  it('sect filter options use sect_name as label', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh',
      messages: {
        zh: {
          game: {
            event_panel: {
              title: 'Events',
              filter_all: 'All',
              filter_all_sects: '所有宗门',
              deceased: '(dead)',
              add_second: '+1',
              load_more: 'load',
              empty_none: 'none',
              empty_single: 'none',
              empty_dual: 'none',
            }
          },
          common: { loading: 'loading', year: '年', month: '月' },
        }
      }
    })

    const wrapper = mount(EventPanel, {
      global: { plugins: [i18n] }
    })

    const sectSelect = wrapper.findComponent(NSelect)
    expect(sectSelect.exists()).toBe(true)
    const options = sectSelect.props('options') as Array<{ label: string; value: string | number }>
    const sectOptions = options.filter(o => o.value !== 'all')
    expect(sectOptions.map(o => o.label)).toContain('青云门')
    expect(sectOptions.map(o => o.label)).toContain('天火宗')
  })

  it('selecting sect filter calls resetEvents with sect_id', async () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh',
      messages: {
        zh: {
          game: {
            event_panel: {
              title: 'Events',
              filter_all: 'All',
              filter_all_sects: '所有宗门',
              deceased: '(dead)',
              add_second: '+1',
              load_more: 'load',
              empty_none: 'none',
              empty_single: 'none',
              empty_dual: 'none',
            }
          },
          common: { loading: 'loading', year: '年', month: '月' },
        }
      }
    })

    const wrapper = mount(EventPanel, {
      global: { plugins: [i18n] }
    })

    const sectSelect = wrapper.findComponent(NSelect)
    expect(sectSelect.exists()).toBe(true)
    await sectSelect.vm.$emit('update:value', 1)
    await wrapper.vm.$nextTick()

    expect(eventStoreMock.resetEvents).toHaveBeenCalledWith(expect.objectContaining({ sect_id: 1 }))
  })
})
