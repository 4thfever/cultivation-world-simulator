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
})
