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
              value: '关系值',
              reasons: '关系理由',
              empty: '暂无关系数据',
              overlap_tiles: '重叠{count}格',
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
                TERRITORY_CONFLICT: '势力范围冲突',
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
          reason_breakdown: [
            { reason: 'ALIGNMENT_OPPOSITE', delta: -40 },
            { reason: 'ORTHODOXY_SAME', delta: 10 },
            { reason: 'TERRITORY_CONFLICT', delta: -2, meta: { overlap_tiles: 1 } },
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
    expect(text).toContain('重叠1格')
  })
})
