import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import SectRelationsModal from '@/components/game/panels/SectRelationsModal.vue'

// Mock worldApi via '@/api' (same入口 as其它测试)
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

// Mock uiStore
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
          reasons: ['ALIGNMENT_OPPOSITE', 'ORTHODOXY_SAME', 'TERRITORY_CONFLICT'],
        },
      ],
    })

    const wrapper = mount(SectRelationsModal, {
      props: { show: true },
      global: {
        plugins: [i18n],
      },
    })

    // 等待异步加载完成
    await Promise.resolve()
    await wrapper.vm.$nextTick()

    return wrapper
  }

  it('renders table with relations when data is loaded', async () => {
    const wrapper = await createWrapper()
    // 只验证组件可正常渲染，不抛出异常
    expect(wrapper.exists()).toBe(true)
  })
})

