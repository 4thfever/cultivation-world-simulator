import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { h, defineComponent, nextTick, ref } from 'vue'
import { setActivePinia, createPinia } from 'pinia'

// Use vi.hoisted to define mock functions that will be used by vi.mock.
const { mockGetPhenomenaList, mockChangePhenomenon, mockSuccess, mockError } = vi.hoisted(() => ({
  mockGetPhenomenaList: vi.fn(),
  mockChangePhenomenon: vi.fn(),
  mockSuccess: vi.fn(),
  mockError: vi.fn(),
}))

const refreshDynastyOverviewMock = vi.hoisted(() => vi.fn())
const refreshAvatarOverviewMock = vi.hoisted(() => vi.fn())

// Mutable store state that can be modified in tests.
let mockYear = 100
let mockMonth = 5
let mockCurrentPhenomenon: any = { id: 1, name: 'Test Phenomenon', rarity: 'R' }
let mockActiveDomains: any[] = []
let mockPhenomenaList: any[] = [
  { id: 1, name: 'Phenomenon 1', rarity: 'N', desc: 'Desc 1', effect_desc: 'Effect 1' },
  { id: 2, name: 'Phenomenon 2', rarity: 'R', desc: 'Desc 2', effect_desc: 'Effect 2' },
  { id: 3, name: 'Phenomenon 3', rarity: 'SSR', desc: 'Desc 3', effect_desc: 'Effect 3' },
]
let mockIsConnected = true
let mockAvatarOverview: any = {
  summary: {
    totalCount: 0,
    aliveCount: 0,
    deadCount: 0,
    sectMemberCount: 0,
    rogueCount: 0,
  },
  realmDistribution: [],
}
let mockAvatarOverviewLoaded = false
const mockFetch = vi.fn()

// Mock vue-i18n.
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    locale: ref('zh-CN'),
    t: (key: string, params?: any) => {
      if (params) return `${key}:${JSON.stringify(params)}`
      return key
    },
  }),
}))

// Mock stores.
vi.mock('@/stores/world', () => ({
  useWorldStore: () => ({
    get year() { return mockYear },
    get month() { return mockMonth },
    get currentPhenomenon() { return mockCurrentPhenomenon },
    get activeDomains() { return mockActiveDomains },
    get phenomenaList() { return mockPhenomenaList },
    getPhenomenaList: mockGetPhenomenaList,
    changePhenomenon: mockChangePhenomenon,
  }),
}))

vi.mock('@/stores/socket', () => ({
  useSocketStore: () => ({
    get isConnected() { return mockIsConnected },
  }),
}))

vi.mock('@/stores/dynasty', () => ({
  useDynastyStore: () => ({
    overview: {
      name: '晋',
      title: '晋朝',
      royal_surname: '司马',
      royal_house_name: '司马氏',
      desc: '门第森然。',
      effect_desc: '',
      is_low_magic: true,
    },
    isLoading: false,
    isLoaded: true,
    refreshOverview: refreshDynastyOverviewMock,
  }),
}))

vi.mock('@/stores/avatarOverview', () => ({
  useAvatarOverviewStore: () => ({
    get overview() { return mockAvatarOverview },
    get isLoaded() { return mockAvatarOverviewLoaded },
    refreshOverview: refreshAvatarOverviewMock,
  }),
}))

// Mock naive-ui.
vi.mock('naive-ui', () => ({
  NModal: defineComponent({
    name: 'NModal',
    props: ['show', 'preset', 'title'],
    emits: ['update:show'],
    setup(props, { slots, emit }) {
      return () => props.show ? h('div', {
        class: 'n-modal-stub',
        onClick: () => emit('update:show', false),
      }, slots.default?.()) : null
    },
  }),
  NList: defineComponent({
    name: 'NList',
    props: ['hoverable', 'clickable'],
    setup(_, { slots }) {
      return () => h('div', { class: 'n-list-stub' }, slots.default?.())
    },
  }),
  NListItem: defineComponent({
    name: 'NListItem',
    emits: ['click'],
    setup(_, { slots, emit }) {
      return () => h('div', {
        class: 'n-list-item-stub',
        onClick: () => emit('click'),
      }, slots.default?.())
    },
  }),
  NTag: defineComponent({
    name: 'NTag',
    props: ['size', 'bordered', 'color'],
    setup(_, { slots }) {
      return () => h('span', { class: 'n-tag-stub' }, slots.default?.())
    },
  }),
  NEmpty: defineComponent({
    name: 'NEmpty',
    props: ['description'],
    setup(props) {
      return () => h('div', { class: 'n-empty-stub' }, props.description)
    },
  }),
  NSpin: defineComponent({
    name: 'NSpin',
    props: ['show'],
    setup(_, { slots }) {
      return () => h('div', { class: 'n-spin-stub' }, slots.default?.())
    },
  }),
  useMessage: () => ({
    success: mockSuccess,
    error: mockError,
  }),
}))

// Stub StatusWidget.
const StatusWidgetStub = defineComponent({
  name: 'StatusWidget',
  props: ['label', 'icon', 'color', 'mode', 'disablePopover', 'title', 'items', 'emptyText'],
  emits: ['trigger-click'],
  setup(props, { emit }) {
    return () => h('div', {
      class: 'status-widget-stub',
      'data-label': props.label,
      'data-icon': props.icon,
      'data-color': props.color,
      onClick: () => emit('trigger-click'),
    }, props.label)
  },
})

import StatusBar from '@/components/layout/StatusBar.vue'

describe('StatusBar', () => {
  const globalConfig = {
    global: {
      directives: {
        sound: () => {}
      },
      stubs: {
        StatusWidget: StatusWidgetStub,
        TimeOverviewModal: true,
        AvatarOverviewModal: true,
      },
    },
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.stubGlobal('fetch', mockFetch)

    // Reset mock values.
    mockYear = 100
    mockMonth = 5
    mockCurrentPhenomenon = { id: 1, name: 'Test Phenomenon', rarity: 'R' }
    mockActiveDomains = []
    mockIsConnected = true
    mockAvatarOverview = {
      summary: {
        totalCount: 0,
        aliveCount: 0,
        deadCount: 0,
        sectMemberCount: 0,
        rogueCount: 0,
      },
      realmDistribution: [],
    }
    mockAvatarOverviewLoaded = false

    // Setup default mock implementations.
    mockGetPhenomenaList.mockImplementation(() => Promise.resolve())
    mockChangePhenomenon.mockImplementation(() => Promise.resolve())
    mockFetch.mockResolvedValue({
      ok: true,
      text: () => Promise.resolve([
        'title,title_id,name_id,desc_id,desc',
        '标题,标题ID,名称ID,描述ID,描述',
        '简介,WORLD_INFO_INTRO_TITLE,WORLD_INFO_INTRO_NAME,WORLD_INFO_INTRO_DESC,这是一个诸多修士竞相修行的修仙世界。',
      ].join('\n')),
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('should display year and month from worldStore', () => {
    mockYear = 200
    mockMonth = 12

    const wrapper = mount(StatusBar, globalConfig)

    expect(wrapper.text()).toContain('200')
    expect(wrapper.text()).toContain('12')
  })

  it('should show connected status when socketStore.isConnected is true', () => {
    mockIsConnected = true

    const wrapper = mount(StatusBar, globalConfig)

    expect(wrapper.find('.status-dot.connected').exists()).toBe(true)
  })

  it('should show disconnected status when socketStore.isConnected is false', () => {
    mockIsConnected = false

    const wrapper = mount(StatusBar, globalConfig)

    expect(wrapper.find('.status-dot.connected').exists()).toBe(false)
    expect(wrapper.find('.status-dot').exists()).toBe(true)
  })

  describe('phenomenonColor', () => {
    it('should return #9aa4b2 for N rarity', () => {
      mockCurrentPhenomenon = { id: 1, name: 'Test', rarity: 'N' }

      const wrapper = mount(StatusBar, globalConfig)

      const widget = wrapper.findAll('.status-widget-stub')[1]
      expect(widget.attributes('data-color')).toBe('#9aa4b2')
    })

    it('should return #63a3ff for R rarity', () => {
      mockCurrentPhenomenon = { id: 1, name: 'Test', rarity: 'R' }

      const wrapper = mount(StatusBar, globalConfig)

      const widget = wrapper.findAll('.status-widget-stub')[1]
      expect(widget.attributes('data-color')).toBe('#63a3ff')
    })

    it('should return #63c28b for SR rarity', () => {
      mockCurrentPhenomenon = { id: 1, name: 'Test', rarity: 'SR' }

      const wrapper = mount(StatusBar, globalConfig)

      const widget = wrapper.findAll('.status-widget-stub')[1]
      expect(widget.attributes('data-color')).toBe('#63c28b')
    })

    it('should return #e1ab52 for SSR rarity', () => {
      mockCurrentPhenomenon = { id: 1, name: 'Test', rarity: 'SSR' }

      const wrapper = mount(StatusBar, globalConfig)

      const widget = wrapper.findAll('.status-widget-stub')[1]
      expect(widget.attributes('data-color')).toBe('#e1ab52')
    })

    it('should return #8c8c8c for unknown rarity', () => {
      mockCurrentPhenomenon = { id: 1, name: 'Test', rarity: 'UNKNOWN' }

      const wrapper = mount(StatusBar, globalConfig)

      const widget = wrapper.findAll('.status-widget-stub')[1]
      expect(widget.attributes('data-color')).toBe('#8c8c8c')
    })

    it('should hide phenomenon widget when currentPhenomenon is null', () => {
      mockCurrentPhenomenon = null

      const wrapper = mount(StatusBar, globalConfig)

      // time + domain/sect-relations/dynasty/mortal/ranking/tournament/avatar-overview/world-info
      const widgets = wrapper.findAll('.status-widget-stub')
      expect(widgets.length).toBe(9)
    })

    it('should place time widget before phenomenon widget and world info widget last', () => {
      const wrapper = mount(StatusBar, globalConfig)

      const widgets = wrapper.findAll('.status-widget-stub')
      expect(widgets[0]?.attributes('data-label')).toBe('100common.year5common.month')
      expect(widgets[0]?.attributes('data-icon')).toBeTruthy()
      expect(widgets[1]?.attributes('data-label')).toBe('[Test Phenomenon]')
      expect(widgets[9]?.attributes('data-label')).toBe('game.status_bar.world_info.label')
    })
  })

  describe('phenomenon selector', () => {
    it('should call getPhenomenaList when opening selector', async () => {
      const wrapper = mount(StatusBar, globalConfig)

      // Trigger click on phenomenon widget.
      await wrapper.findAll('.status-widget-stub')[1].trigger('click')

      // Run all pending timers and promises.
      await vi.runAllTimersAsync()
      await nextTick()

      expect(mockGetPhenomenaList).toHaveBeenCalled()
    })

    it('should show selector modal after getPhenomenaList', async () => {
      const wrapper = mount(StatusBar, globalConfig)

      await wrapper.findAll('.status-widget-stub')[1].trigger('click')
      await vi.runAllTimersAsync()
      await nextTick()

      expect(wrapper.find('.n-modal-stub').exists()).toBe(true)
    })
  })

  describe('changePhenomenon', () => {
    it('should call changePhenomenon on selection', async () => {
      const wrapper = mount(StatusBar, globalConfig)

      // Open selector.
      await wrapper.findAll('.status-widget-stub')[1].trigger('click')
      await vi.runAllTimersAsync()
      await nextTick()

      // Find and click a list item.
      const listItems = wrapper.findAll('.n-list-item-stub')
      expect(listItems.length).toBeGreaterThan(0)

      await listItems[0].trigger('click')
      await vi.runAllTimersAsync()
      await nextTick()

      expect(mockChangePhenomenon).toHaveBeenCalled()
    })

    it('should show success message on successful change', async () => {
      mockChangePhenomenon.mockImplementation(() => Promise.resolve())

      const wrapper = mount(StatusBar, globalConfig)

      await wrapper.findAll('.status-widget-stub')[1].trigger('click')
      await vi.runAllTimersAsync()
      await nextTick()

      const listItems = wrapper.findAll('.n-list-item-stub')
      expect(listItems.length).toBeGreaterThan(0)

      await listItems[0].trigger('click')
      await vi.runAllTimersAsync()
      await nextTick()

      expect(mockSuccess).toHaveBeenCalled()
    })

    it('should show error message on failed change', async () => {
      mockChangePhenomenon.mockImplementation(() => Promise.reject(new Error('Failed')))

      const wrapper = mount(StatusBar, globalConfig)

      await wrapper.findAll('.status-widget-stub')[1].trigger('click')
      await vi.runAllTimersAsync()
      await nextTick()

      const listItems = wrapper.findAll('.n-list-item-stub')
      expect(listItems.length).toBeGreaterThan(0)

      await listItems[0].trigger('click')
      await vi.runAllTimersAsync()
      await nextTick()

      expect(mockError).toHaveBeenCalled()
    })
  })

  describe('domain color', () => {
    it('should use the same hidden domain color when any domain is open', () => {
      mockActiveDomains = [
        { id: 1, name: 'D1' },
        { id: 2, name: 'D2' },
      ]

      const wrapper = mount(StatusBar, globalConfig)

      const domainWidget = wrapper.findAll('.status-widget-stub')[2]
      expect(domainWidget.attributes('data-color')).toBe('#b78a52')
    })

    it('should use the same hidden domain color when all domains are closed', () => {
      mockActiveDomains = [
        { id: 1, name: 'D1' },
        { id: 2, name: 'D2' },
      ]

      const wrapper = mount(StatusBar, globalConfig)

      const domainWidget = wrapper.findAll('.status-widget-stub')[2]
      expect(domainWidget.attributes('data-color')).toBe('#b78a52')
    })

    it('should use the same hidden domain color when there are no domains', () => {
      mockActiveDomains = []

      const wrapper = mount(StatusBar, globalConfig)

      const domainWidget = wrapper.findAll('.status-widget-stub')[2]
      expect(domainWidget.attributes('data-color')).toBe('#b78a52')
    })
  })

  it('should render external links', () => {
    const wrapper = mount(StatusBar, globalConfig)

    const links = wrapper.findAll('a.author-link')
    expect(links.length).toBe(1)
    expect(links[0].attributes('href')).toContain('github')
  })

  it('should pass correct props to phenomenon StatusWidget', () => {
    mockCurrentPhenomenon = { id: 1, name: 'TestPhenomenon', rarity: 'SR' }

    const wrapper = mount(StatusBar, globalConfig)

    const phenomenonWidget = wrapper.findAll('.status-widget-stub')[1]
    expect(phenomenonWidget.attributes('data-label')).toBe('[TestPhenomenon]')
    expect(phenomenonWidget.attributes('data-color')).toBe('#63c28b')
  })

  it('should pass correct props to domain StatusWidget', () => {
    const wrapper = mount(StatusBar, globalConfig)

    const domainWidget = wrapper.findAll('.status-widget-stub')[2]
    expect(domainWidget.attributes('data-label')).toBe('game.status_bar.hidden_domain.label')
  })

  it('should render sect relations StatusWidget', () => {
    const wrapper = mount(StatusBar, globalConfig)

    const widgets = wrapper.findAll('.status-widget-stub')
    // time + currentPhenomenon + domain + sect_relations + dynasty + mortal + ranking + tournament + avatar-overview + world-info
    expect(widgets.length).toBe(10)
    const sectRelationsWidget = widgets[3]
    expect(sectRelationsWidget.attributes('data-label')).toBe('game.sect_relations.title_short')
  })

  it('should render dynasty StatusWidget', () => {
    const wrapper = mount(StatusBar, globalConfig)

    const widgets = wrapper.findAll('.status-widget-stub')
    const dynastyWidget = widgets[4]
    expect(dynastyWidget.attributes('data-label')).toBe('game.dynasty.title_short')
  })

  it('should render deceased StatusWidget', () => {
    const wrapper = mount(StatusBar, globalConfig)

    const widgets = wrapper.findAll('.status-widget-stub')
    const deceasedWidget = widgets[8]
    expect(deceasedWidget.attributes('data-label')).toBe('game.status_bar.avatar_overview.label')
    expect(deceasedWidget.attributes('data-color')).toBe('#8c8c8c')
  })

  it('should keep avatar overview label fixed when loaded', () => {
    mockAvatarOverviewLoaded = true
    mockAvatarOverview = {
      summary: {
        totalCount: 128,
        aliveCount: 93,
        deadCount: 35,
        sectMemberCount: 70,
        rogueCount: 23,
      },
      realmDistribution: [],
    }

    const wrapper = mount(StatusBar, globalConfig)

    const widgets = wrapper.findAll('.status-widget-stub')
    const overviewWidget = widgets[8]
    expect(overviewWidget.attributes('data-label')).toBe('game.status_bar.avatar_overview.label')
  })

  it('should fetch avatar overview before opening modal if not loaded', async () => {
    const wrapper = mount(StatusBar, globalConfig)

    await wrapper.findAll('.status-widget-stub')[8].trigger('click')
    await nextTick()

    expect(refreshAvatarOverviewMock).toHaveBeenCalled()
  })
})
