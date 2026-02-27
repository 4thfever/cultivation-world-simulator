import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { h, defineComponent, nextTick } from 'vue'
import { setActivePinia, createPinia } from 'pinia'

// Use vi.hoisted to define mock functions that will be used by vi.mock.
const { mockGetPhenomenaList, mockChangePhenomenon, mockSuccess, mockError } = vi.hoisted(() => ({
  mockGetPhenomenaList: vi.fn(),
  mockChangePhenomenon: vi.fn(),
  mockSuccess: vi.fn(),
  mockError: vi.fn(),
}))

// Mutable store state that can be modified in tests.
let mockYear = 100
let mockMonth = 5
let mockCurrentPhenomenon: any = { id: 1, name: 'Test Phenomenon', rarity: 'R' }
let mockActiveDomains: any[] = []
let mockAvatarList: any[] = [{ id: '1' }, { id: '2' }]
let mockPhenomenaList: any[] = [
  { id: 1, name: 'Phenomenon 1', rarity: 'N', desc: 'Desc 1', effect_desc: 'Effect 1' },
  { id: 2, name: 'Phenomenon 2', rarity: 'R', desc: 'Desc 2', effect_desc: 'Effect 2' },
  { id: 3, name: 'Phenomenon 3', rarity: 'SSR', desc: 'Desc 3', effect_desc: 'Effect 3' },
]
let mockIsConnected = true

// Mock vue-i18n.
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
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
    get avatarList() { return mockAvatarList },
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
  useMessage: () => ({
    success: mockSuccess,
    error: mockError,
  }),
}))

// Stub StatusWidget.
const StatusWidgetStub = defineComponent({
  name: 'StatusWidget',
  props: ['label', 'color', 'mode', 'disablePopover', 'title', 'items', 'emptyText'],
  emits: ['trigger-click'],
  setup(props, { emit }) {
    return () => h('div', {
      class: 'status-widget-stub',
      'data-label': props.label,
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
      },
    },
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()

    // Reset mock values.
    mockYear = 100
    mockMonth = 5
    mockCurrentPhenomenon = { id: 1, name: 'Test Phenomenon', rarity: 'R' }
    mockActiveDomains = []
    mockAvatarList = [{ id: '1' }, { id: '2' }]
    mockIsConnected = true

    // Setup default mock implementations.
    mockGetPhenomenaList.mockImplementation(() => Promise.resolve())
    mockChangePhenomenon.mockImplementation(() => Promise.resolve())
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
    it('should return #ccc for N rarity', () => {
      mockCurrentPhenomenon = { id: 1, name: 'Test', rarity: 'N' }

      const wrapper = mount(StatusBar, globalConfig)

      const widget = wrapper.findAll('.status-widget-stub')[0]
      expect(widget.attributes('data-color')).toBe('#ccc')
    })

    it('should return #4dabf7 for R rarity', () => {
      mockCurrentPhenomenon = { id: 1, name: 'Test', rarity: 'R' }

      const wrapper = mount(StatusBar, globalConfig)

      const widget = wrapper.findAll('.status-widget-stub')[0]
      expect(widget.attributes('data-color')).toBe('#4dabf7')
    })

    it('should return #a0d911 for SR rarity', () => {
      mockCurrentPhenomenon = { id: 1, name: 'Test', rarity: 'SR' }

      const wrapper = mount(StatusBar, globalConfig)

      const widget = wrapper.findAll('.status-widget-stub')[0]
      expect(widget.attributes('data-color')).toBe('#a0d911')
    })

    it('should return #fa8c16 for SSR rarity', () => {
      mockCurrentPhenomenon = { id: 1, name: 'Test', rarity: 'SSR' }

      const wrapper = mount(StatusBar, globalConfig)

      const widget = wrapper.findAll('.status-widget-stub')[0]
      expect(widget.attributes('data-color')).toBe('#fa8c16')
    })

    it('should return #ccc for unknown rarity', () => {
      mockCurrentPhenomenon = { id: 1, name: 'Test', rarity: 'UNKNOWN' }

      const wrapper = mount(StatusBar, globalConfig)

      const widget = wrapper.findAll('.status-widget-stub')[0]
      expect(widget.attributes('data-color')).toBe('#ccc')
    })

    it('should hide phenomenon widget when currentPhenomenon is null', () => {
      mockCurrentPhenomenon = null

      const wrapper = mount(StatusBar, globalConfig)

      // When phenomenon is null, v-if hides the widget.
      // Domain widget and Ranking widget should exist.
      const widgets = wrapper.findAll('.status-widget-stub')
      expect(widgets.length).toBe(2)
    })
  })

  describe('phenomenon selector', () => {
    it('should call getPhenomenaList when opening selector', async () => {
      const wrapper = mount(StatusBar, globalConfig)

      // Trigger click on phenomenon widget.
      await wrapper.findAll('.status-widget-stub')[0].trigger('click')

      // Run all pending timers and promises.
      await vi.runAllTimersAsync()
      await nextTick()

      expect(mockGetPhenomenaList).toHaveBeenCalled()
    })

    it('should show selector modal after getPhenomenaList', async () => {
      const wrapper = mount(StatusBar, globalConfig)

      await wrapper.findAll('.status-widget-stub')[0].trigger('click')
      await vi.runAllTimersAsync()
      await nextTick()

      expect(wrapper.find('.n-modal-stub').exists()).toBe(true)
    })
  })

  describe('changePhenomenon', () => {
    it('should call changePhenomenon on selection', async () => {
      const wrapper = mount(StatusBar, globalConfig)

      // Open selector.
      await wrapper.findAll('.status-widget-stub')[0].trigger('click')
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

      await wrapper.findAll('.status-widget-stub')[0].trigger('click')
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

      await wrapper.findAll('.status-widget-stub')[0].trigger('click')
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
    it('should return #fa8c16 when any domain is open', () => {
      mockActiveDomains = [
        { id: 1, name: 'D1', is_open: false },
        { id: 2, name: 'D2', is_open: true },
      ]

      const wrapper = mount(StatusBar, globalConfig)

      const domainWidget = wrapper.findAll('.status-widget-stub')[1]
      expect(domainWidget.attributes('data-color')).toBe('#fa8c16')
    })

    it('should return #666 when all domains are closed', () => {
      mockActiveDomains = [
        { id: 1, name: 'D1', is_open: false },
        { id: 2, name: 'D2', is_open: false },
      ]

      const wrapper = mount(StatusBar, globalConfig)

      const domainWidget = wrapper.findAll('.status-widget-stub')[1]
      expect(domainWidget.attributes('data-color')).toBe('#666')
    })

    it('should return #666 when no domains', () => {
      mockActiveDomains = []

      const wrapper = mount(StatusBar, globalConfig)

      const domainWidget = wrapper.findAll('.status-widget-stub')[1]
      expect(domainWidget.attributes('data-color')).toBe('#666')
    })
  })

  it('should display cultivator count', () => {
    mockAvatarList = [{ id: '1' }, { id: '2' }, { id: '3' }]

    const wrapper = mount(StatusBar, globalConfig)

    // The t function returns key:params format.
    expect(wrapper.text()).toContain('game.status_bar.cultivators')
  })

  it('should render external links', () => {
    const wrapper = mount(StatusBar, globalConfig)

    const links = wrapper.findAll('a.author-link')
    expect(links.length).toBe(2)
    expect(links[0].attributes('href')).toContain('bilibili')
    expect(links[1].attributes('href')).toContain('github')
  })

  it('should pass correct props to phenomenon StatusWidget', () => {
    mockCurrentPhenomenon = { id: 1, name: 'TestPhenomenon', rarity: 'SR' }

    const wrapper = mount(StatusBar, globalConfig)

    const phenomenonWidget = wrapper.findAll('.status-widget-stub')[0]
    expect(phenomenonWidget.attributes('data-label')).toBe('[TestPhenomenon]')
    expect(phenomenonWidget.attributes('data-color')).toBe('#a0d911')
  })

  it('should pass correct props to domain StatusWidget', () => {
    const wrapper = mount(StatusBar, globalConfig)

    const domainWidget = wrapper.findAll('.status-widget-stub')[1]
    expect(domainWidget.attributes('data-label')).toBe('game.status_bar.hidden_domain.label')
  })
})
