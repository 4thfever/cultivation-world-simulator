import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import MortalOverviewModal from '@/components/game/panels/MortalOverviewModal.vue'

const refreshOverviewMock = vi.fn()

vi.mock('naive-ui', () => ({
  NModal: {
    name: 'NModal',
    template: '<div v-if="show" class="n-modal"><slot /></div>',
    props: ['show', 'title', 'preset'],
  },
  NTable: {
    name: 'NTable',
    template: '<table><slot /></table>',
    props: ['bordered', 'singleLine', 'size'],
  },
  NTag: {
    name: 'NTag',
    template: '<span class="n-tag"><slot /></span>',
    props: ['bordered', 'type', 'size'],
  },
  NSpin: {
    name: 'NSpin',
    template: '<div class="n-spin"><slot /></div>',
    props: ['show'],
  },
}))

vi.mock('@/stores/mortal', () => ({
  useMortalStore: () => ({
    overview: {
      summary: {
        total_population: 140.0,
        total_population_capacity: 250.0,
        total_natural_growth: 1.74,
        tracked_mortal_count: 2,
        awakening_candidate_count: 1,
      },
      cities: [
        { id: 1, name: '青石城', population: 100.0, population_capacity: 200.0, natural_growth: 1.5 },
      ],
      tracked_mortals: [
        {
          id: 'm1',
          name: '赵行舟',
          gender: 'male',
          age: 20,
          born_region_id: 1,
          born_region_name: '青石城',
          parents: ['a', 'b'],
          is_awakening_candidate: true,
        },
      ],
    },
    isLoading: false,
    isLoaded: true,
    refreshOverview: refreshOverviewMock,
  }),
}))

describe('MortalOverviewModal', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  function createWrapper(show = true) {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {
        'zh-CN': {
          game: {
            mortal_system: {
              title: '凡人系统',
              empty: '暂无数据',
              population_value: '{value} 万',
              population_growth_value: '{value} 万/月',
              population_ratio_value: '{current} / {capacity} 万',
              summary: {
                title: '世界统计',
                total_population: '总人口',
                total_capacity: '总容量',
                total_growth: '总自然增长量',
              },
              cities: {
                title: '城市统计',
                city: '城市',
                population: '人口',
                capacity: '容量',
                growth: '自然增长量',
              },
              tracked: {
                title: '被追踪凡人',
                count: '被追踪凡人数',
                awakening_candidates: '觉醒候选数',
                name: '姓名',
                gender: '性别',
                age: '年龄',
                birth_region: '出生地',
                unknown_region: '未知',
              },
            },
          },
        },
      },
    })

    return mount(MortalOverviewModal, {
      props: { show },
      global: {
        plugins: [i18n],
      },
    })
  }

  it('fetches overview when opened', async () => {
    const wrapper = createWrapper(false)
    await wrapper.setProps({ show: true })
    expect(refreshOverviewMock).toHaveBeenCalled()
  })

  it('renders summary, city stats, and tracked mortals', () => {
    const wrapper = createWrapper(true)
    const text = wrapper.text()
    expect(text).toContain('总人口')
    expect(text).toContain('140.0 万')
    expect(text).toContain('青石城')
    expect(text).toContain('+1.50 万/月')
    expect(text).toContain('赵行舟')
    expect(text).toContain('male')
  })

  it('renders English population with compact units instead of ten-thousand', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'en-US',
      messages: {
        'en-US': {
          game: {
            mortal_system: {
              title: 'Mortal System',
              empty: 'No data',
              population_value: '{value}',
              population_growth_value: '{value}/month',
              population_ratio_value: '{current} / {capacity}',
              summary: {
                title: 'World Overview',
                total_population: 'Total Population',
                total_capacity: 'Total Capacity',
                total_growth: 'Total Natural Growth',
              },
              cities: {
                title: 'City Overview',
                city: 'City',
                population: 'Population',
                capacity: 'Capacity',
                growth: 'Natural Growth',
              },
              tracked: {
                title: 'Tracked Mortals',
                count: 'Tracked Mortals',
                awakening_candidates: 'Awakening Candidates',
                name: 'Name',
                gender: 'Gender',
                age: 'Age',
                birth_region: 'Birth Region',
                unknown_region: 'Unknown',
              },
            },
          },
        },
      },
    })

    const wrapper = mount(MortalOverviewModal, {
      props: { show: true },
      global: {
        plugins: [i18n],
      },
    })

    const text = wrapper.text()
    expect(text).toContain('1.4M')
    expect(text).toContain('+17.4K/month')
    expect(text).not.toContain('ten-thousand')
  })
})
