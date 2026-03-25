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
  isLoaded: true,
})

const sectStoreMock = reactive({
  activeSectOptions: [
    { label: '青云门', value: 1 },
    { label: '天火宗', value: 2 },
  ],
  isLoaded: true,
  isLoading: false,
  refreshTerritories: vi.fn(async () => {}),
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

vi.mock('@/stores/sect', () => ({
  useSectStore: () => sectStoreMock,
}))

function createEventPanelI18n(locale = 'zh') {
  return createI18n({
    legacy: false,
    locale,
    messages: {
      zh: {
        game: {
          event_panel: {
            title: 'Events',
            filter_all: 'All',
            filter_all_sects: '所有宗门',
            filter_event_scope_all: '所有事',
            filter_event_scope_major: '大事',
            filter_event_scope_minor: '小事',
            deceased: '(dead)',
            load_more: 'load',
            empty_none: 'none',
            empty_single: 'none',
          },
          event_templates: {
            nickname_awarded: '{avatar_name} is now "{nickname}".',
          },
        },
        common: { loading: 'loading', year: '年', month: '月' },
      },
      vi: {
        game: {
          event_panel: {
            title: 'Events',
            filter_all: 'All',
            filter_all_sects: 'All sects',
            filter_event_scope_all: 'All events',
            filter_event_scope_major: 'Major',
            filter_event_scope_minor: 'Minor',
            deceased: '(dead)',
            load_more: 'load',
            empty_none: 'none',
            empty_single: 'none',
          },
          event_templates: {
            nickname_awarded: '{avatar_name} da duoc goi la "{nickname}".',
          },
        },
        common: { loading: 'loading', year: 'Nam', month: 'Thang' },
      },
    },
  })
}

describe('EventPanel', () => {
  beforeEach(() => {
    eventStoreMock.events = []
    eventStoreMock.eventsHasMore = false
    eventStoreMock.eventsLoading = false
    eventStoreMock.resetEvents.mockClear()
    eventStoreMock.loadMoreEvents.mockClear()
    uiStoreMock.select.mockClear()
    sectStoreMock.refreshTerritories.mockClear()
    sectStoreMock.activeSectOptions = [
      { label: '青云门', value: 1 },
      { label: '天火宗', value: 2 },
    ]
    sectStoreMock.isLoaded = true
    sectStoreMock.isLoading = false
    mapStoreMock.regions = new Map([
      ['r1', { id: 'r1', name: '明心山', type: 'sect', sect_id: 1, sect_name: '青云门', sect_color: '#4DD0E1', x: 10, y: 10 }],
      ['r2', { id: 'r2', name: '赤焰峰', type: 'sect', sect_id: 2, sect_name: '天火宗', sect_color: '#8D6E63', x: 20, y: 20 }],
    ])
  })

  it('should render successfully', () => {
    const i18n = createEventPanelI18n()

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
    const i18n = createEventPanelI18n()

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
    const i18n = createEventPanelI18n()

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

  it('should render structured event text from locale template', () => {
    const i18n = createEventPanelI18n('vi')

    eventStoreMock.events = [
      {
        id: 'e3',
        text: '',
        content: 'Old fallback content',
        year: 105,
        month: 12,
        timestamp: 1272,
        relatedAvatarIds: ['a1'],
        isMajor: true,
        isStory: false,
        renderKey: 'nickname_awarded',
        renderParams: {
          avatar_name: 'Alice',
          nickname: 'Xich Huyet Thanh Dia Chu',
        },
      },
    ]

    const wrapper = mount(EventPanel, {
      global: { plugins: [i18n] },
    })

    expect(wrapper.text()).toContain('Alice da duoc goi la "Xich Huyet Thanh Dia Chu".')
    expect(wrapper.text()).not.toContain('Old fallback content')
  })

  it('sect filter options use sect_name as label', () => {
    const i18n = createEventPanelI18n()

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

  it('sect filter options only include active sects', () => {
    sectStoreMock.activeSectOptions = [
      { label: '青云门', value: 1 },
    ]

    const i18n = createEventPanelI18n()

    const wrapper = mount(EventPanel, {
      global: { plugins: [i18n] }
    })

    const sectSelect = wrapper.findComponent(NSelect)
    const options = sectSelect.props('options') as Array<{ label: string; value: string | number }>
    const sectOptions = options.filter(o => o.value !== 'all')
    expect(sectOptions.map(o => o.label)).toEqual(['青云门'])
  })

  it('selecting sect filter calls resetEvents with sect_id', async () => {
    const i18n = createEventPanelI18n()

    const wrapper = mount(EventPanel, {
      global: { plugins: [i18n] }
    })

    const sectSelect = wrapper.findComponent(NSelect)
    expect(sectSelect.exists()).toBe(true)
    await sectSelect.vm.$emit('update:value', 1)
    await wrapper.vm.$nextTick()

    expect(eventStoreMock.resetEvents).toHaveBeenCalledWith(expect.objectContaining({ sect_id: 1 }))
  })

  it('major filter options render all three scopes', () => {
    const i18n = createEventPanelI18n()

    const wrapper = mount(EventPanel, {
      global: { plugins: [i18n] }
    })

    const selects = wrapper.findAllComponents(NSelect)
    const majorSelect = selects[selects.length - 1]
    const options = majorSelect.props('options') as Array<{ label: string; value: string }>
    expect(options).toEqual([
      { label: '所有事', value: 'all' },
      { label: '大事', value: 'major' },
      { label: '小事', value: 'minor' },
    ])
  })

  it('changing major filter calls resetEvents with major_scope', async () => {
    const i18n = createEventPanelI18n()

    const wrapper = mount(EventPanel, {
      global: { plugins: [i18n] }
    })

    const selects = wrapper.findAllComponents(NSelect)
    const majorSelect = selects[selects.length - 1]
    expect(majorSelect.exists()).toBe(true)
    await majorSelect.vm.$emit('update:value', 'major')
    await wrapper.vm.$nextTick()

    expect(eventStoreMock.resetEvents).toHaveBeenCalledWith(expect.objectContaining({ major_scope: 'major' }))
  })
})
