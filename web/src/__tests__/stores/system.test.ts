import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useSystemStore } from '@/stores/system'
import type { InitStatusDTO } from '@/types/api'

// Mock the API module.
vi.mock('@/api', () => ({
  systemApi: {
    fetchInitStatus: vi.fn(),
    pauseGame: vi.fn(),
    resumeGame: vi.fn(),
  },
}))

import { systemApi } from '@/api'

const createMockStatus = (overrides: Partial<InitStatusDTO> = {}): InitStatusDTO => ({
  status: 'idle',
  phase: 0,
  phase_name: '',
  progress: 0,
  elapsed_seconds: 0,
  error: null,
  llm_check_failed: false,
  llm_error_message: '',
  ...overrides,
})

describe('useSystemStore', () => {
  let store: ReturnType<typeof useSystemStore>

  beforeEach(() => {
    store = useSystemStore()
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have correct initial values', () => {
      expect(store.initStatus).toBeNull()
      expect(store.isInitialized).toBe(false)
      expect(store.isManualPaused).toBe(true)
      expect(store.isGameRunning).toBe(false)
    })
  })

  describe('isLoading', () => {
    it('should return true when initStatus is null', () => {
      expect(store.isLoading).toBe(true)
    })

    it('should return false when status is idle', () => {
      store.initStatus = createMockStatus({ status: 'idle', progress: 0 })
      expect(store.isLoading).toBe(false)
    })

    it('should return true when status is in_progress', () => {
      store.initStatus = createMockStatus({ status: 'in_progress', progress: 50 })
      expect(store.isLoading).toBe(true)
    })

    it('should return false when status is ready and initialized', () => {
      store.initStatus = createMockStatus({ status: 'ready', progress: 100 })
      store.setInitialized(true)
      expect(store.isLoading).toBe(false)
    })

    it('should return true when status is error', () => {
      store.initStatus = createMockStatus({ status: 'error' as any, progress: 0 })
      expect(store.isLoading).toBe(true)
    })
  })

  describe('isReady', () => {
    it('should return false when not initialized', () => {
      store.initStatus = createMockStatus({ status: 'ready', progress: 100 })
      expect(store.isReady).toBe(false)
    })

    it('should return true when status is ready and initialized', () => {
      store.initStatus = createMockStatus({ status: 'ready', progress: 100 })
      store.setInitialized(true)
      expect(store.isReady).toBe(true)
    })
  })

  describe('togglePause', () => {
    it('should toggle from paused to playing and call resumeGame', async () => {
      store.isManualPaused = true
      vi.mocked(systemApi.resumeGame).mockResolvedValue(undefined)

      await store.togglePause()

      expect(store.isManualPaused).toBe(false)
      expect(systemApi.resumeGame).toHaveBeenCalled()
    })

    it('should toggle from playing to paused and call pauseGame', async () => {
      store.isManualPaused = false
      vi.mocked(systemApi.pauseGame).mockResolvedValue(undefined)

      await store.togglePause()

      expect(store.isManualPaused).toBe(true)
      expect(systemApi.pauseGame).toHaveBeenCalled()
    })

    it('should rollback state on API failure', async () => {
      store.isManualPaused = true
      vi.mocked(systemApi.resumeGame).mockRejectedValue(new Error('API error'))

      await store.togglePause()

      // Should rollback to original state.
      expect(store.isManualPaused).toBe(true)
    })
  })

  describe('setInitialized', () => {
    it('should set isInitialized value', () => {
      store.setInitialized(true)
      expect(store.isInitialized).toBe(true)

      store.setInitialized(false)
      expect(store.isInitialized).toBe(false)
    })
  })

  describe('fetchInitStatus', () => {
    it('should update initStatus on success', async () => {
      const mockStatus = createMockStatus({ status: 'ready', progress: 100 })
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(mockStatus)

      const result = await store.fetchInitStatus()

      expect(result).toEqual(mockStatus)
      expect(store.initStatus).toEqual(mockStatus)
    })

    it('should set isGameRunning to true when status is ready', async () => {
      const mockStatus = createMockStatus({ status: 'ready', progress: 100 })
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(mockStatus)

      await store.fetchInitStatus()

      expect(store.isGameRunning).toBe(true)
    })

    it('should set isGameRunning to false when status is not ready', async () => {
      const mockStatus = createMockStatus({ status: 'in_progress', progress: 50 })
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(mockStatus)

      await store.fetchInitStatus()

      expect(store.isGameRunning).toBe(false)
    })

    it('should return null and log error on failure', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(systemApi.fetchInitStatus).mockRejectedValue(new Error('Network error'))

      const result = await store.fetchInitStatus()

      expect(result).toBeNull()
      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })

    it('should ignore stale response when called rapidly (race condition fix)', async () => {
      // Scenario:
      // 1. fetchInitStatus() called, request R1 starts (slow, returns 'in_progress')
      // 2. fetchInitStatus() called again, request R2 starts (fast, returns 'ready')
      // 3. R2 returns first -> initStatus = 'ready', isGameRunning = true
      // 4. R1 returns later -> should be ignored (requestId mismatch)
      
      let resolveR1: (value: any) => void
      const r1Promise = new Promise(resolve => { resolveR1 = resolve })
      
      let callCount = 0
      vi.mocked(systemApi.fetchInitStatus).mockImplementation(async () => {
        callCount++
        if (callCount === 1) {
          await r1Promise
          return createMockStatus({ status: 'in_progress', progress: 50 })
        }
        return createMockStatus({ status: 'ready', progress: 100 })
      })

      // Start R1 (slow)
      const fetch1 = store.fetchInitStatus()
      
      // Start R2 (fast) - this should be the "truth"
      const result2 = await store.fetchInitStatus()
      expect(result2?.status).toBe('ready')
      expect(store.initStatus?.status).toBe('ready')
      expect(store.isGameRunning).toBe(true)
      
      // R1 completes with stale data - should be ignored
      resolveR1!(undefined)
      const result1 = await fetch1
      
      // Stale response should return null and not update state
      expect(result1).toBeNull()
      expect(store.initStatus?.status).toBe('ready') // Still fresh data
      expect(store.isGameRunning).toBe(true) // Still correct
    })
  })

  describe('pause', () => {
    it('should call pauseGame API', async () => {
      vi.mocked(systemApi.pauseGame).mockResolvedValue(undefined)

      await store.pause()

      expect(systemApi.pauseGame).toHaveBeenCalled()
    })

    it('should not modify isManualPaused state', async () => {
      store.isManualPaused = false
      vi.mocked(systemApi.pauseGame).mockResolvedValue(undefined)

      await store.pause()

      expect(store.isManualPaused).toBe(false)
    })

    it('should log error on failure', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(systemApi.pauseGame).mockRejectedValue(new Error('API error'))

      await store.pause()

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })

  describe('resume', () => {
    it('should call resumeGame API', async () => {
      vi.mocked(systemApi.resumeGame).mockResolvedValue(undefined)

      await store.resume()

      expect(systemApi.resumeGame).toHaveBeenCalled()
    })

    it('should not modify isManualPaused state', async () => {
      store.isManualPaused = true
      vi.mocked(systemApi.resumeGame).mockResolvedValue(undefined)

      await store.resume()

      expect(store.isManualPaused).toBe(true)
    })

    it('should log error on failure', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(systemApi.resumeGame).mockRejectedValue(new Error('API error'))

      await store.resume()

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })

  describe('isGameRunning', () => {
    it('should have initial value of false', () => {
      expect(store.isGameRunning).toBe(false)
    })
  })
})
