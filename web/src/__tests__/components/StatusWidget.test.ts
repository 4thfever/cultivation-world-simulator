import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { h, defineComponent } from 'vue'

// Mock vue-i18n.
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
  }),
}))

// Mock naive-ui with stub components.
vi.mock('naive-ui', () => ({
  NPopover: defineComponent({
    name: 'NPopover',
    props: ['trigger', 'placement'],
    setup(_, { slots }) {
      return () => h('div', { class: 'n-popover-stub' }, [
        slots.trigger?.(),
        slots.default?.(),
      ])
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
    setup(_, { slots }) {
      return () => h('div', { class: 'n-list-item-stub' }, slots.default?.())
    },
  }),
  NTag: defineComponent({
    name: 'NTag',
    props: ['size', 'bordered', 'type'],
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
}))

import StatusWidget from '@/components/layout/StatusWidget.vue'

describe('StatusWidget', () => {
  const defaultProps = {
    label: 'Test Label',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render label', () => {
    const wrapper = mount(StatusWidget, {
      props: defaultProps,
    })

    expect(wrapper.text()).toContain('Test Label')
  })

  it('should render label with custom color', () => {
    const wrapper = mount(StatusWidget, {
      props: {
        ...defaultProps,
        color: '#ff0000',
      },
    })

    const trigger = wrapper.find('.widget-trigger')
    expect(trigger.attributes('style')).toContain('color: rgb(255, 0, 0)')
  })

  it('should use default color when not provided', () => {
    const wrapper = mount(StatusWidget, {
      props: defaultProps,
    })

    const trigger = wrapper.find('.widget-trigger')
    expect(trigger.attributes('style')).toContain('color: rgb(204, 204, 204)')
  })

  it('should emit trigger-click when clicked', async () => {
    const wrapper = mount(StatusWidget, {
      props: defaultProps,
    })

    await wrapper.find('.widget-trigger').trigger('click')

    expect(wrapper.emitted('trigger-click')).toBeTruthy()
    expect(wrapper.emitted('trigger-click')?.length).toBe(1)
  })

  describe('with disablePopover', () => {
    it('should skip popover when disablePopover is true', () => {
      const wrapper = mount(StatusWidget, {
        props: {
          ...defaultProps,
          disablePopover: true,
        },
      })

      // Should not have popover wrapper.
      expect(wrapper.find('.n-popover-stub').exists()).toBe(false)
      // But should still have trigger.
      expect(wrapper.find('.widget-trigger').exists()).toBe(true)
    })

    it('should emit trigger-click when disablePopover is true', async () => {
      const wrapper = mount(StatusWidget, {
        props: {
          ...defaultProps,
          disablePopover: true,
        },
      })

      await wrapper.find('.widget-trigger').trigger('click')

      expect(wrapper.emitted('trigger-click')).toBeTruthy()
    })
  })

  describe('list mode', () => {
    const domainItems = [
      {
        id: 1,
        name: 'Domain One',
        desc: 'Description one',
        is_open: true,
        max_realm: 'Level 5',
        danger_prob: 0.3,
        drop_prob: 0.5,
        cd_years: 10,
        open_prob: 0.1,
      },
      {
        id: 2,
        name: 'Domain Two',
        desc: 'Description two',
        is_open: false,
        max_realm: 'Level 3',
        danger_prob: 0.2,
        drop_prob: 0.4,
        cd_years: 5,
        open_prob: 0.2,
      },
    ]

    it('should render list mode with items', () => {
      const wrapper = mount(StatusWidget, {
        props: {
          ...defaultProps,
          mode: 'list',
          items: domainItems,
          title: 'Domain List',
        },
      })

      expect(wrapper.find('.list-header').text()).toBe('Domain List')
      expect(wrapper.findAll('.n-list-item-stub').length).toBe(2)
    })

    it('should show empty state when no items', () => {
      const wrapper = mount(StatusWidget, {
        props: {
          ...defaultProps,
          mode: 'list',
          items: [],
          emptyText: 'No data available',
        },
      })

      expect(wrapper.find('.n-empty-stub').exists()).toBe(true)
      expect(wrapper.find('.n-empty-stub').text()).toBe('No data available')
    })

    it('should use default emptyText when not provided', () => {
      const wrapper = mount(StatusWidget, {
        props: {
          ...defaultProps,
          mode: 'list',
          items: [],
        },
      })

      // Default is Chinese text from props defaults.
      expect(wrapper.find('.n-empty-stub').exists()).toBe(true)
    })

    it('should render domain item details', () => {
      const wrapper = mount(StatusWidget, {
        props: {
          ...defaultProps,
          mode: 'list',
          items: [domainItems[0]],
        },
      })

      expect(wrapper.text()).toContain('Domain One')
      expect(wrapper.text()).toContain('Description one')
      expect(wrapper.text()).toContain('30%') // danger_prob formatted.
      expect(wrapper.text()).toContain('50%') // drop_prob formatted.
    })

    it('should apply is-closed class for closed domains', () => {
      const wrapper = mount(StatusWidget, {
        props: {
          ...defaultProps,
          mode: 'list',
          items: [domainItems[1]], // is_open: false.
        },
      })

      expect(wrapper.find('.domain-item.is-closed').exists()).toBe(true)
    })

    it('should not apply is-closed class for open domains', () => {
      const wrapper = mount(StatusWidget, {
        props: {
          ...defaultProps,
          mode: 'list',
          items: [domainItems[0]], // is_open: true.
        },
      })

      expect(wrapper.find('.domain-item.is-closed').exists()).toBe(false)
    })
  })

  describe('single mode', () => {
    it('should render single mode slot', () => {
      const wrapper = mount(StatusWidget, {
        props: {
          ...defaultProps,
          mode: 'single',
        },
        slots: {
          single: '<div class="custom-single">Custom Content</div>',
        },
      })

      expect(wrapper.find('.custom-single').exists()).toBe(true)
      expect(wrapper.text()).toContain('Custom Content')
    })
  })

  it('should render divider', () => {
    const wrapper = mount(StatusWidget, {
      props: defaultProps,
    })

    expect(wrapper.find('.divider').exists()).toBe(true)
    expect(wrapper.find('.divider').text()).toBe('|')
  })

  it('should handle title in list mode', () => {
    const wrapper = mount(StatusWidget, {
      props: {
        ...defaultProps,
        mode: 'list',
        title: 'Custom Title',
        items: [{ id: 1, name: 'Test', desc: '', is_open: true, max_realm: '', danger_prob: 0, drop_prob: 0, cd_years: 0, open_prob: 0 }],
      },
    })

    expect(wrapper.find('.list-header').text()).toBe('Custom Title')
  })

  it('should hide title when not provided', () => {
    const wrapper = mount(StatusWidget, {
      props: {
        ...defaultProps,
        mode: 'list',
        items: [],
      },
    })

    expect(wrapper.find('.list-header').exists()).toBe(false)
  })
})
