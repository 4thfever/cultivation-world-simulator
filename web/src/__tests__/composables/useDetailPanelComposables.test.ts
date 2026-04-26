import { defineComponent, nextTick, reactive } from 'vue'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { avatarApi } from '@/api'
import { useAvatarPortraitPanel } from '@/composables/useAvatarPortraitPanel'
import { useRankingModal } from '@/composables/useRankingModal'
import { useRegionDetailPanel } from '@/composables/useRegionDetailPanel'
import type { RegionDetail } from '@/types/core'

const messageMock = {
  success: vi.fn(),
  error: vi.fn(),
}

const selectMock = vi.fn()
const updateAvatarSummaryMock = vi.fn()
const fetchRankingsMock = vi.fn()
const rankingsMock = reactive({
  heaven: [],
  earth: [],
  human: [],
  sect: [],
  tournament: null,
})

vi.mock('naive-ui', () => ({
  useMessage: () => messageMock,
}))

vi.mock('@/api', () => ({
  avatarApi: {
    fetchAvatarMeta: vi.fn(),
    updateAvatarPortrait: vi.fn(),
  },
}))

vi.mock('@/stores/ui', () => ({
  useUiStore: () => ({
    select: selectMock,
  }),
}))

vi.mock('@/stores/avatar', () => ({
  useAvatarStore: () => ({
    updateAvatarSummary: updateAvatarSummaryMock,
  }),
}))

vi.mock('@/composables/useWorldOverviewData', () => ({
  useWorldOverviewData: () => ({
    loading: { value: false },
    rankings: rankingsMock,
    fetchRankings: fetchRankingsMock,
  }),
}))

const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  messages: {
    'zh-CN': {
      attributes: {
        FIRE: '火',
        WATER: '水',
      },
      game: {
        info_panel: {
          region: {
            type_explanations: {
              city: '城市说明',
              ruin: '遗迹说明',
              cave: '洞府说明',
              sect: '宗门说明',
              normal: '普通区域说明',
            },
          },
          avatar: {
            portrait: {
              load_failed: '加载失败',
              apply_failed: '应用失败',
              apply_success: '应用成功',
            },
          },
        },
      },
    },
  },
})

function mountComposable<T>(factory: () => T): T {
  let result!: T
  mount(defineComponent({
    setup() {
      result = factory()
      return () => null
    },
  }), {
    global: {
      plugins: [i18n],
    },
  })
  return result
}

async function settle() {
  await Promise.resolve()
  await Promise.resolve()
  await nextTick()
}

describe('detail panel composables', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('formats region details and routes entity jumps', () => {
    const region = reactive<RegionDetail>({
      id: 'r1',
      name: '洞府',
      type: 'cultivate',
      sub_type: 'ruin',
      type_name: '遗迹',
      desc: '古老遗迹',
      animals: [],
      plants: [],
      lodes: [],
    })

    const panel = mountComposable(() => useRegionDetailPanel(() => region))

    expect(panel.formatEssenceType('fire, water, custom')).toBe('火、水、custom')
    expect(panel.getRegionTypeExplanation()).toBe('遗迹说明')
    expect(panel.getPopulationBarColor(0.9)).toBe('#52c41a')

    panel.jumpToSect(12)
    panel.jumpToAvatar('a1')
    expect(selectMock).toHaveBeenCalledWith('sect', '12')
    expect(selectMock).toHaveBeenCalledWith('avatar', 'a1')
  })

  it('loads and applies avatar portrait changes', async () => {
    vi.mocked(avatarApi.fetchAvatarMeta).mockResolvedValue({
      males: [1, 2],
      females: [3, 4],
    })
    vi.mocked(avatarApi.updateAvatarPortrait).mockResolvedValue({ success: true })
    const props = reactive({
      avatarId: 'a1',
      gender: 'female',
      currentPicId: 3,
      visible: true,
    })
    const emit = vi.fn()

    const panel = mountComposable(() => useAvatarPortraitPanel(props, emit))
    await settle()

    expect(panel.availableAvatars.value).toEqual([3, 4])
    panel.selectedPicId.value = 4
    await panel.handleApply()

    expect(avatarApi.updateAvatarPortrait).toHaveBeenCalledWith({ avatar_id: 'a1', pic_id: 4 })
    expect(updateAvatarSummaryMock).toHaveBeenCalledWith('a1', { pic_id: 4 })
    expect(messageMock.success).toHaveBeenCalledWith('应用成功')
    expect(emit).toHaveBeenCalledWith('updated')
    expect(emit).toHaveBeenCalledWith('close')
  })

  it('refreshes rankings when initially mounted open and closes after navigation', async () => {
    const state = reactive({ show: true })
    const close = vi.fn(() => {
      state.show = false
    })
    const panel = mountComposable(() => useRankingModal(() => state.show, close))

    await nextTick()
    expect(fetchRankingsMock).toHaveBeenCalledTimes(1)

    panel.openAvatarInfo('a2')
    panel.openSectInfo('s1')
    expect(selectMock).toHaveBeenCalledWith('avatar', 'a2')
    expect(selectMock).toHaveBeenCalledWith('sect', 's1')
    expect(close).toHaveBeenCalledTimes(2)
  })
})
