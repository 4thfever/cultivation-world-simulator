import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Create mock functions at module level.
const mockOn = vi.fn(() => vi.fn())
const mockOnStatusChange = vi.fn(() => vi.fn())
const mockConnect = vi.fn()
const mockDisconnect = vi.fn()

// Mock the gameSocket before imports.
vi.mock('@/api/socket', () => ({
  gameSocket: {
    on: () => mockOn(),
    onStatusChange: () => mockOnStatusChange(),
    connect: () => mockConnect(),
    disconnect: () => mockDisconnect(),
  },
}))

// Mock world and ui stores.
const mockWorldStore = {
  handleTick: vi.fn(),
  initialize: vi.fn().mockResolvedValue(undefined),
}

const mockUiStore = {
  selectedTarget: null as { type: string; id: string } | null,
  refreshDetail: vi.fn(),
}

vi.mock('@/stores/world', () => ({
  useWorldStore: () => mockWorldStore,
}))

vi.mock('@/stores/ui', () => ({
  useUiStore: () => mockUiStore,
}))

import { useSocketStore } from '@/stores/socket'

describe('useSocketStore', () => {
  let store: ReturnType<typeof useSocketStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useSocketStore()
    
    // Reset mocks.
    vi.clearAllMocks()
    mockUiStore.selectedTarget = null
    mockOn.mockReturnValue(vi.fn())
    mockOnStatusChange.mockReturnValue(vi.fn())
  })

  afterEach(() => {
    store.disconnect()
  })

  describe('initial state', () => {
    it('should have correct initial values', () => {
      expect(store.isConnected).toBe(false)
      expect(store.lastError).toBeNull()
    })
  })

  describe('init', () => {
    it('should connect on init', () => {
      store.init()

      expect(mockConnect).toHaveBeenCalled()
    })
  })

  describe('disconnect', () => {
    it('should disconnect and set isConnected to false', () => {
      store.init()
      store.disconnect()

      expect(mockDisconnect).toHaveBeenCalled()
      expect(store.isConnected).toBe(false)
    })

    it('should be safe to call multiple times', () => {
      store.disconnect()
      store.disconnect()

      // Should not throw.
      expect(mockDisconnect).toHaveBeenCalledTimes(2)
    })
  })

  describe('isConnected', () => {
    it('should start as false', () => {
      expect(store.isConnected).toBe(false)
    })
  })

  describe('lastError', () => {
    it('should start as null', () => {
      expect(store.lastError).toBeNull()
    })
  })
})
