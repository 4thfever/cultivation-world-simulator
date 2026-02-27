import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RelationRow from '@/components/game/panels/info/components/RelationRow.vue'

describe('RelationRow', () => {
  const defaultProps = {
    name: 'Test Name',
  }

  const globalConfig = {
    directives: {
      sound: () => {}
    }
  }

  it('should render name prop', () => {
    const wrapper = mount(RelationRow, {
      props: defaultProps,
      global: globalConfig,
    })

    expect(wrapper.text()).toContain('Test Name')
    expect(wrapper.find('.rel-name').text()).toBe('Test Name')
  })

  it('should render meta when provided', () => {
    const wrapper = mount(RelationRow, {
      props: {
        ...defaultProps,
        meta: 'Test Meta',
      },
      global: globalConfig,
    })

    expect(wrapper.find('.rel-type').exists()).toBe(true)
    expect(wrapper.find('.rel-type').text()).toBe('Test Meta')
  })

  it('should hide meta when not provided', () => {
    const wrapper = mount(RelationRow, {
      props: defaultProps,
      global: globalConfig,
    })

    expect(wrapper.find('.rel-type').exists()).toBe(false)
  })

  it('should render sub when provided', () => {
    const wrapper = mount(RelationRow, {
      props: {
        ...defaultProps,
        sub: 'Subtitle text',
      },
      global: globalConfig,
    })

    expect(wrapper.find('.rel-sub').exists()).toBe(true)
    expect(wrapper.find('.rel-sub').text()).toBe('Subtitle text')
  })

  it('should hide sub when not provided', () => {
    const wrapper = mount(RelationRow, {
      props: defaultProps,
      global: globalConfig,
    })

    expect(wrapper.find('.rel-sub').exists()).toBe(false)
  })

  it('should emit click on click', async () => {
    const wrapper = mount(RelationRow, {
      props: defaultProps,
      global: globalConfig,
    })

    await wrapper.find('.relation-row').trigger('click')

    expect(wrapper.emitted('click')).toBeTruthy()
    expect(wrapper.emitted('click')?.length).toBe(1)
  })

  it('should emit multiple clicks', async () => {
    const wrapper = mount(RelationRow, {
      props: defaultProps,
      global: globalConfig,
    })

    await wrapper.find('.relation-row').trigger('click')
    await wrapper.find('.relation-row').trigger('click')
    await wrapper.find('.relation-row').trigger('click')

    expect(wrapper.emitted('click')?.length).toBe(3)
  })

  it('should render all props together', () => {
    const wrapper = mount(RelationRow, {
      props: {
        name: 'Full Name',
        meta: 'Meta Info',
        sub: 'Sub Info',
      },
      global: globalConfig,
    })

    expect(wrapper.find('.rel-name').text()).toBe('Full Name')
    expect(wrapper.find('.rel-type').text()).toBe('Meta Info')
    expect(wrapper.find('.rel-sub').text()).toBe('Sub Info')
  })
})
