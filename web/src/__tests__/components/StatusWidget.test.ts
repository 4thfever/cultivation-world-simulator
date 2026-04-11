import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { h, defineComponent } from 'vue'

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
}))

import StatusWidget from '@/components/layout/StatusWidget.vue'

const soundDirective = {
  mounted() {},
}

describe('StatusWidget', () => {
  const defaultProps = {
    label: 'Test Label',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the label', () => {
    const wrapper = mount(StatusWidget, {
      props: defaultProps,
      global: {
        directives: {
          sound: soundDirective,
        },
      },
    })

    expect(wrapper.text()).toContain('Test Label')
  })

  it('renders the icon when icon url is provided', () => {
    const wrapper = mount(StatusWidget, {
      props: {
        ...defaultProps,
        icon: '/icons/test.svg',
      },
      global: {
        directives: {
          sound: soundDirective,
        },
      },
    })

    const icon = wrapper.find('.widget-icon')
    expect(icon.exists()).toBe(true)
    expect(icon.attributes('style')).toContain('url(/icons/test.svg)')
  })

  it('renders the label with custom color', () => {
    const wrapper = mount(StatusWidget, {
      props: {
        ...defaultProps,
        color: '#ff0000',
      },
      global: {
        directives: {
          sound: soundDirective,
        },
      },
    })

    const trigger = wrapper.find('.widget-trigger')
    expect(trigger.attributes('style')).toContain('color: rgb(255, 0, 0)')
  })

  it('uses the default color when not provided', () => {
    const wrapper = mount(StatusWidget, {
      props: defaultProps,
      global: {
        directives: {
          sound: soundDirective,
        },
      },
    })

    const trigger = wrapper.find('.widget-trigger')
    expect(trigger.attributes('style')).toContain('color: rgb(204, 204, 204)')
  })

  it('emits trigger-click when clicked', async () => {
    const wrapper = mount(StatusWidget, {
      props: defaultProps,
      global: {
        directives: {
          sound: soundDirective,
        },
      },
    })

    await wrapper.find('.widget-trigger').trigger('click')

    expect(wrapper.emitted('trigger-click')).toBeTruthy()
    expect(wrapper.emitted('trigger-click')?.length).toBe(1)
  })

  it('skips popover when disablePopover is true', () => {
    const wrapper = mount(StatusWidget, {
      props: {
        ...defaultProps,
        disablePopover: true,
      },
      global: {
        directives: {
          sound: soundDirective,
        },
      },
    })

    expect(wrapper.find('.n-popover-stub').exists()).toBe(false)
    expect(wrapper.find('.widget-trigger').exists()).toBe(true)
  })

  it('renders the single slot inside popover mode', () => {
    const wrapper = mount(StatusWidget, {
      props: defaultProps,
      slots: {
        single: '<div class="custom-single">Custom Content</div>',
      },
      global: {
        directives: {
          sound: soundDirective,
        },
      },
    })

    expect(wrapper.find('.custom-single').exists()).toBe(true)
    expect(wrapper.text()).toContain('Custom Content')
  })

  it('renders the divider', () => {
    const wrapper = mount(StatusWidget, {
      props: defaultProps,
      global: {
        directives: {
          sound: soundDirective,
        },
      },
    })

    expect(wrapper.find('.divider').exists()).toBe(true)
    expect(wrapper.find('.divider').text()).toBe('|')
  })
})
