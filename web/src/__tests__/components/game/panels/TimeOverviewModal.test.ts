import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { nextTick } from 'vue'
import TimeOverviewModal from '@/components/game/panels/TimeOverviewModal.vue'

vi.mock('naive-ui', () => ({
  NModal: {
    name: 'NModal',
    template: '<div v-if="show" class="n-modal"><slot /></div>',
    props: ['show', 'title', 'preset'],
  },
  NSpin: {
    name: 'NSpin',
    template: '<div class="n-spin"><slot /></div>',
    props: ['show'],
  },
}))

vi.mock('@/api/modules/world', () => ({
  worldApi: {
    fetchRankings: vi.fn(),
    fetchSectRelations: vi.fn(),
  },
}))

const worldStoreMock = {
  year: 103,
  month: 5,
  elapsedMonths: 29,
  currentPhenomenon: { id: 1, name: '灵气潮汐', rarity: 'SR' },
}

vi.mock('@/stores/world', () => ({
  useWorldStore: () => worldStoreMock,
}))

import { worldApi } from '@/api/modules/world'

describe('TimeOverviewModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    worldStoreMock.year = 103
    worldStoreMock.month = 5
    worldStoreMock.elapsedMonths = 29
    worldStoreMock.currentPhenomenon = { id: 1, name: '灵气潮汐', rarity: 'SR' }
  })

  function createWrapper() {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {
        'zh-CN': {
          game: {
            status_bar: {
              time: {
                title: '时间总览',
                current_date: '当前日期',
                current_date_value: '第 {year} 年 {month} 月',
                elapsed: '本局历时',
                elapsed_months_only: '已运行 {months} 个月',
                elapsed_years_only: '已运行 {years} 年',
                elapsed_years_months: '已运行 {years} 年 {months} 个月',
                phenomenon: '当前天象',
                no_phenomenon: '暂无天象',
                tournament: '下次论道/大比',
                no_tournament: '暂无论道/大比信息',
                sect_war: '宗门战争',
                war_active: '当前有 {count} 场宗门战争',
                war_none: '当前无宗门战争',
              },
            },
            ranking: {
              tournament_next: '距离下一届还有 {years} 年',
            },
          },
        },
      },
    })

    return mount(TimeOverviewModal, {
      props: { show: false },
      global: {
        plugins: [i18n],
      },
    })
  }

  it('renders the five overview items after loading data', async () => {
    vi.mocked(worldApi.fetchRankings).mockResolvedValue({
      heaven: [],
      earth: [],
      human: [],
      sect: [],
      tournament: { next_year: 110 },
    })
    vi.mocked(worldApi.fetchSectRelations).mockResolvedValue({
      relations: [
        {
          sect_a_id: 1,
          sect_a_name: '青云宗',
          sect_b_id: 2,
          sect_b_name: '赤炎宗',
          value: -30,
          diplomacy_status: 'war',
          diplomacy_duration_months: 12,
          reason_breakdown: [],
        },
        {
          sect_a_id: 3,
          sect_a_name: '玄心宗',
          sect_b_id: 4,
          sect_b_name: '北斗宗',
          value: 20,
          diplomacy_status: 'peace',
          diplomacy_duration_months: 8,
          reason_breakdown: [],
        },
      ],
    })

    const wrapper = createWrapper()
    await wrapper.setProps({ show: true })
    await Promise.resolve()
    await nextTick()

    const text = wrapper.text()
    expect(text).toContain('第 103 年 5 月')
    expect(text).toContain('已运行 2 年 5 个月')
    expect(text).toContain('灵气潮汐')
    expect(text).toContain('距离下一届还有 7 年')
    expect(text).toContain('当前有 1 场宗门战争')
  })

  it('shows empty-style fallback text when no phenomenon or no war exists', async () => {
    worldStoreMock.currentPhenomenon = null
    vi.mocked(worldApi.fetchRankings).mockResolvedValue({
      heaven: [],
      earth: [],
      human: [],
      sect: [],
    })
    vi.mocked(worldApi.fetchSectRelations).mockResolvedValue({
      relations: [],
    })

    const wrapper = createWrapper()
    await wrapper.setProps({ show: true })
    await Promise.resolve()
    await nextTick()

    const text = wrapper.text()
    expect(text).toContain('暂无天象')
    expect(text).toContain('暂无论道/大比信息')
    expect(text).toContain('当前无宗门战争')
  })
})
