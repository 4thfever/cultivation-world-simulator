import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAvatarOverviewStore } from '@/stores/avatarOverview'

vi.mock('@/api', () => ({
  worldApi: {
    fetchAvatarOverview: vi.fn(),
  },
}))

import { worldApi } from '@/api'

describe('useAvatarOverviewStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('loads avatar overview data', async () => {
    vi.mocked(worldApi.fetchAvatarOverview).mockResolvedValue({
      summary: {
        totalCount: 12,
        aliveCount: 9,
        deadCount: 3,
        sectMemberCount: 7,
        rogueCount: 2,
      },
      realmDistribution: [{ realm: '练气', count: 6 }],
    })

    const store = useAvatarOverviewStore()
    await store.refreshOverview()

    expect(store.isLoaded).toBe(true)
    expect(store.overview.summary.totalCount).toBe(12)
    expect(store.overview.realmDistribution).toHaveLength(1)
  })

  it('falls back to empty overview when api fails', async () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.mocked(worldApi.fetchAvatarOverview).mockRejectedValue(new Error('Network error'))

    const store = useAvatarOverviewStore()
    await store.refreshOverview()

    expect(store.isLoaded).toBe(false)
    expect(store.overview.summary.totalCount).toBe(0)
    consoleSpy.mockRestore()
  })
})
