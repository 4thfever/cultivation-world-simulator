import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import StatItem from '@/components/game/panels/info/components/StatItem.vue'

describe('StatItem', () => {
  const defaultProps = {
    label: 'Test Label',
    value: 'Test Value',
  }

  it('should render label', () => {
    const wrapper = mount(StatItem, {
      props: defaultProps,
    })

    expect(wrapper.find('label').text()).toBe('Test Label')
  })

  it('should render string value', () => {
    const wrapper = mount(StatItem, {
      props: defaultProps,
    })

    expect(wrapper.find('span').text()).toContain('Test Value')
  })

  it('should render numeric value', () => {
    const wrapper = mount(StatItem, {
      props: {
        label: 'Count',
        value: 42,
      },
    })

    expect(wrapper.find('span').text()).toContain('42')
  })

  it('should render subValue when provided', () => {
    const wrapper = mount(StatItem, {
      props: {
        ...defaultProps,
        subValue: 'Sub Info',
      },
    })

    expect(wrapper.find('.sub-value').exists()).toBe(true)
    expect(wrapper.find('.sub-value').text()).toBe('(Sub Info)')
  })

  it('should render numeric subValue', () => {
    const wrapper = mount(StatItem, {
      props: {
        ...defaultProps,
        subValue: 100,
      },
    })

    expect(wrapper.find('.sub-value').text()).toBe('(100)')
  })

  it('should hide subValue when not provided', () => {
    const wrapper = mount(StatItem, {
      props: defaultProps,
    })

    expect(wrapper.find('.sub-value').exists()).toBe(false)
  })

  it('should have clickable class when onClick provided', () => {
    const onClick = vi.fn()
    const wrapper = mount(StatItem, {
      props: {
        ...defaultProps,
        onClick,
      },
    })

    expect(wrapper.find('.stat-item').classes()).toContain('clickable')
  })

  it('should not have clickable class when onClick not provided', () => {
    const wrapper = mount(StatItem, {
      props: defaultProps,
    })

    expect(wrapper.find('.stat-item').classes()).not.toContain('clickable')
  })

  it('should call onClick when clicked', async () => {
    const onClick = vi.fn()
    const wrapper = mount(StatItem, {
      props: {
        ...defaultProps,
        onClick,
      },
    })

    await wrapper.find('.stat-item').trigger('click')

    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('should not throw when clicked without onClick', async () => {
    const wrapper = mount(StatItem, {
      props: defaultProps,
    })

    // Should not throw.
    await wrapper.find('.stat-item').trigger('click')
  })

  it('should have full class when fullWidth is true', () => {
    const wrapper = mount(StatItem, {
      props: {
        ...defaultProps,
        fullWidth: true,
      },
    })

    expect(wrapper.find('.stat-item').classes()).toContain('full')
  })

  it('should not have full class when fullWidth is false', () => {
    const wrapper = mount(StatItem, {
      props: {
        ...defaultProps,
        fullWidth: false,
      },
    })

    expect(wrapper.find('.stat-item').classes()).not.toContain('full')
  })

  it('should not have full class when fullWidth not provided', () => {
    const wrapper = mount(StatItem, {
      props: defaultProps,
    })

    expect(wrapper.find('.stat-item').classes()).not.toContain('full')
  })

  it('should render all props together', () => {
    const onClick = vi.fn()
    const wrapper = mount(StatItem, {
      props: {
        label: 'Full Label',
        value: 'Full Value',
        subValue: 'Full Sub',
        onClick,
        fullWidth: true,
      },
    })

    expect(wrapper.find('label').text()).toBe('Full Label')
    expect(wrapper.find('span').text()).toContain('Full Value')
    expect(wrapper.find('.sub-value').text()).toBe('(Full Sub)')
    expect(wrapper.find('.stat-item').classes()).toContain('clickable')
    expect(wrapper.find('.stat-item').classes()).toContain('full')
  })
})
