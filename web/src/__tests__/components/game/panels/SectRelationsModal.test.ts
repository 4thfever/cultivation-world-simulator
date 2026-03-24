import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import SectRelationsModal from '@/components/game/panels/SectRelationsModal.vue'

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
    props: ['size', 'bordered'],
  },
  NSpin: {
    name: 'NSpin',
    template: '<div class="n-spin"><slot /></div>',
    props: ['show'],
  },
}))

vi.mock('@/api', () => ({
  worldApi: {
    fetchInitialState: vi.fn(),
    fetchMap: vi.fn(),
    fetchPhenomenaList: vi.fn(),
    setPhenomenon: vi.fn(),
    fetchSectRelations: vi.fn(),
  },
  eventApi: {
    fetchEvents: vi.fn(),
  },
}))

const selectMock = vi.fn()
vi.mock('@/stores/ui', () => ({
  useUiStore: () => ({
    select: selectMock,
  }),
}))

import { worldApi } from '@/api'

describe('SectRelationsModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const createWrapper = async () => {
    const flushPromises = () => Promise.resolve()
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {
        'zh-CN': {
          game: {
            sect_relations: {
              title: '宗门关系',
              sect_a: '宗门 A',
              sect_b: '宗门 B',
              status: '外交状态',
              value: '关系值',
              reasons: '关系理由',
              empty: '暂无关系数据',
              status_war: '战争中',
              status_peace: '和平',
              duration_months: '{count}个月',
              overlap_tiles: '接壤{count}边',
              value_label_very_hostile: '极恶',
              value_label_hostile: '敌对',
              value_label_neutral: '中立',
              value_label_friendly: '友善',
              value_label_very_friendly: '极善',
              reasons_map: {
                ALIGNMENT_OPPOSITE: '阵营不同',
                ALIGNMENT_SAME: '阵营相同',
                ORTHODOXY_DIFFERENT: '道统不同',
                ORTHODOXY_SAME: '道统相同',
                TERRITORY_CONFLICT: '边界压力',
                WAR_STATE: '战争状态',
                PEACE_STATE: '和平状态',
                LONG_PEACE: '长期和平',
              },
            },
          },
        },
      },
    })

    vi.mocked(worldApi.fetchSectRelations).mockResolvedValue({
      relations: [
        {
          sect_a_id: 1,
          sect_a_name: '正道宗',
          sect_b_id: 2,
          sect_b_name: '魔道宗',
          value: -32,
          diplomacy_status: 'war',
          diplomacy_duration_months: 18,
          reason_breakdown: [
            { reason: 'ALIGNMENT_OPPOSITE', delta: -40 },
            { reason: 'ORTHODOXY_SAME', delta: 10 },
            { reason: 'WAR_STATE', delta: -20, meta: { status: 'war', war_months: 18 } },
            { reason: 'TERRITORY_CONFLICT', delta: -2, meta: { border_contact_edges: 1 } },
          ],
        },
      ],
    })

    const wrapper = mount(SectRelationsModal, {
      props: { show: false },
      global: {
        plugins: [i18n],
      },
    })

    await wrapper.setProps({ show: true })
    await flushPromises()
    await wrapper.vm.$nextTick()
    return wrapper
  }

  it('renders reason and per-reason delta when data is loaded', async () => {
    const wrapper = await createWrapper()
    expect(wrapper.exists()).toBe(true)
    const text = wrapper.text()
    expect(text).toContain('阵营不同')
    expect(text).toContain('-40')
    expect(text).toContain('道统相同')
    expect(text).toContain('+10')
    expect(text).toContain('战争中')
    expect(text).toContain('接壤1边')
  })

  it('does not render peace-state reason tag text when status column already shows peace', async () => {
    vi.mocked(worldApi.fetchSectRelations).mockResolvedValueOnce({
      relations: [
        {
          sect_a_id: 1,
          sect_a_name: '正道宗',
          sect_b_id: 2,
          sect_b_name: '清虚宗',
          value: 12,
          diplomacy_status: 'peace',
          diplomacy_duration_months: 16,
          reason_breakdown: [
            { reason: 'PEACE_STATE', delta: 0, meta: { status: 'peace', peace_months: 16 } },
            { reason: 'LONG_PEACE', delta: 1, meta: { status: 'peace', peace_months: 16 } },
          ],
        },
      ],
    })

    const wrapper = await createWrapper()
    const text = wrapper.text()
    expect(text).toContain('和平')
    expect(text).toContain('长期和平')
    expect(text).not.toContain('和平状态')
    expect(text).not.toContain('长期和平 (16个月)')
  })
})
