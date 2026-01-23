import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useUiStore } from '@/stores/ui'
import type { AvatarDetail, RegionDetail, SectDetail } from '@/types/core'

// Mock the API module.
vi.mock('@/api', () => ({
  avatarApi: {
    fetchDetailInfo: vi.fn(),
  },
}))

import { avatarApi } from '@/api'

const createMockAvatarDetail = (overrides: Partial<AvatarDetail> = {}): AvatarDetail => ({
  id: 'avatar-1',
  name: 'Test Avatar',
  gender: 'male',
  realm: 'Qi Refinement',
  age: 25,
  lifespan: 100,
  pos_x: 10,
  pos_y: 20,
  is_alive: true,
  sect_id: null,
  ...overrides,
} as AvatarDetail)

describe('useUiStore', () => {
  let store: ReturnType<typeof useUiStore>

  beforeEach(() => {
    store = useUiStore()
    store.clearSelection()
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have correct initial values', () => {
      expect(store.selectedTarget).toBeNull()
      expect(store.detailData).toBeNull()
      expect(store.isLoadingDetail).toBe(false)
      expect(store.detailError).toBeNull()
    })
  })

  describe('select', () => {
    it('should set selectedTarget and fetch detail', async () => {
      const mockDetail = createMockAvatarDetail()
      vi.mocked(avatarApi.fetchDetailInfo).mockResolvedValue(mockDetail)

      await store.select('avatar', 'avatar-1')

      expect(store.selectedTarget).toEqual({ type: 'avatar', id: 'avatar-1' })
      expect(avatarApi.fetchDetailInfo).toHaveBeenCalledWith({ type: 'avatar', id: 'avatar-1' })
      expect(store.detailData).toEqual(mockDetail)
    })

    it('should not refetch if same target is already selected', async () => {
      store.selectedTarget = { type: 'avatar', id: 'avatar-1' }

      await store.select('avatar', 'avatar-1')

      expect(avatarApi.fetchDetailInfo).not.toHaveBeenCalled()
    })

    it('should clear previous detail data before fetching', async () => {
      store.detailData = createMockAvatarDetail({ id: 'old' })
      vi.mocked(avatarApi.fetchDetailInfo).mockResolvedValue(createMockAvatarDetail({ id: 'new' }))

      const selectPromise = store.select('avatar', 'new')
      
      // Detail should be cleared immediately.
      expect(store.detailData).toBeNull()
      
      await selectPromise
    })

    it('should handle different selection types', async () => {
      vi.mocked(avatarApi.fetchDetailInfo).mockResolvedValue({} as RegionDetail)

      await store.select('region', 'region-1')

      expect(store.selectedTarget).toEqual({ type: 'region', id: 'region-1' })
    })
  })

  describe('clearSelection', () => {
    it('should clear all selection state', () => {
      store.selectedTarget = { type: 'avatar', id: 'avatar-1' }
      store.detailData = createMockAvatarDetail()
      store.detailError = 'Some error'

      store.clearSelection()

      expect(store.selectedTarget).toBeNull()
      expect(store.detailData).toBeNull()
      expect(store.detailError).toBeNull()
    })
  })

  describe('clearHoverCache', () => {
    it('should clear detailData only', () => {
      store.selectedTarget = { type: 'avatar', id: 'avatar-1' }
      store.detailData = createMockAvatarDetail()

      store.clearHoverCache()

      expect(store.selectedTarget).toEqual({ type: 'avatar', id: 'avatar-1' })
      expect(store.detailData).toBeNull()
    })
  })

  describe('refreshDetail', () => {
    it('should do nothing if no target selected', async () => {
      store.selectedTarget = null

      await store.refreshDetail()

      expect(avatarApi.fetchDetailInfo).not.toHaveBeenCalled()
    })

    it('should fetch detail for current target', async () => {
      store.selectedTarget = { type: 'avatar', id: 'avatar-1' }
      const mockDetail = createMockAvatarDetail()
      vi.mocked(avatarApi.fetchDetailInfo).mockResolvedValue(mockDetail)

      await store.refreshDetail()

      expect(avatarApi.fetchDetailInfo).toHaveBeenCalledWith({ type: 'avatar', id: 'avatar-1' })
      expect(store.detailData).toEqual(mockDetail)
    })

    it('should set loading state during fetch', async () => {
      store.selectedTarget = { type: 'avatar', id: 'avatar-1' }
      let loadingDuringFetch = false
      
      vi.mocked(avatarApi.fetchDetailInfo).mockImplementation(async () => {
        loadingDuringFetch = store.isLoadingDetail
        return createMockAvatarDetail()
      })

      await store.refreshDetail()

      expect(loadingDuringFetch).toBe(true)
      expect(store.isLoadingDetail).toBe(false)
    })

    it('should set error on fetch failure', async () => {
      store.selectedTarget = { type: 'avatar', id: 'avatar-1' }
      vi.mocked(avatarApi.fetchDetailInfo).mockRejectedValue(new Error('Network error'))

      await store.refreshDetail()

      expect(store.detailError).toBe('Network error')
      expect(store.isLoadingDetail).toBe(false)
    })

    it('should set generic error message for non-Error exceptions', async () => {
      store.selectedTarget = { type: 'avatar', id: 'avatar-1' }
      vi.mocked(avatarApi.fetchDetailInfo).mockRejectedValue('string error')

      await store.refreshDetail()

      expect(store.detailError).toBe('Failed to load detail')
      expect(store.isLoadingDetail).toBe(false)
    })

    it('should handle race condition - ignore stale response when selection changes to different target', async () => {
      store.selectedTarget = { type: 'avatar', id: 'avatar-1' }
      
      // Simulate slow response.
      vi.mocked(avatarApi.fetchDetailInfo).mockImplementation(async (target) => {
        // During the fetch, selection changes to a DIFFERENT target.
        if (target.id === 'avatar-1') {
          store.selectedTarget = { type: 'avatar', id: 'avatar-2' }
        }
        return createMockAvatarDetail({ id: target.id })
      })

      await store.refreshDetail()

      // Response for avatar-1 should be ignored since selection changed.
      expect(store.detailData).toBeNull()
    })

    it('should ignore stale response when reselecting same target (race condition fix)', async () => {
      // Scenario:
      // 1. User selects avatar-1, request A1 starts (slow)
      // 2. User selects avatar-2, request B starts
      // 3. User selects avatar-1 again, request A2 starts (fast)
      // 4. A2 returns -> updates detailData (correct)
      // 5. A1 returns -> should be ignored (requestId mismatch)

      let callCount = 0
      const responses: { [key: string]: any } = {}

      vi.mocked(avatarApi.fetchDetailInfo).mockImplementation(async (target) => {
        callCount++
        const response = createMockAvatarDetail({ id: target.id, name: `Response_${callCount}` })
        responses[`call_${callCount}`] = response
        return response
      })

      // First select - call 1.
      await store.select('avatar', 'avatar-1')
      expect(store.detailData?.name).toBe('Response_1')

      // Second select (different target) - call 2.
      await store.select('avatar', 'avatar-2')
      expect(store.detailData?.name).toBe('Response_2')

      // Third select (back to original) - call 3.
      await store.select('avatar', 'avatar-1')
      expect(store.detailData?.name).toBe('Response_3')

      // requestId mechanism ensures only the latest response is used.
      expect(callCount).toBe(3)
    })

    it('should clear previous error on new fetch', async () => {
      store.selectedTarget = { type: 'avatar', id: 'avatar-1' }
      store.detailError = 'Previous error'
      vi.mocked(avatarApi.fetchDetailInfo).mockResolvedValue(createMockAvatarDetail())

      await store.refreshDetail()

      expect(store.detailError).toBeNull()
    })
  })

  describe('selection types', () => {
    it('should support avatar selection', async () => {
      vi.mocked(avatarApi.fetchDetailInfo).mockResolvedValue(createMockAvatarDetail())

      await store.select('avatar', 'a1')

      expect(store.selectedTarget?.type).toBe('avatar')
    })

    it('should support region selection', async () => {
      vi.mocked(avatarApi.fetchDetailInfo).mockResolvedValue({} as RegionDetail)

      await store.select('region', 'r1')

      expect(store.selectedTarget?.type).toBe('region')
    })

    it('should support sect selection', async () => {
      vi.mocked(avatarApi.fetchDetailInfo).mockResolvedValue({} as SectDetail)

      await store.select('sect', 's1')

      expect(store.selectedTarget?.type).toBe('sect')
    })
  })
})
