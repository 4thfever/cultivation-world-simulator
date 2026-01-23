import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Create mock functions at module level.
const mockOn = vi.fn(() => vi.fn())
const mockOnStatusChange = vi.fn(() => vi.fn())
const mockConnect = vi.fn()
const mockDisconnect = vi.fn()

// Store callbacks for testing message handling.
let messageCallback: ((data: any) => void) | null = null
let statusCallback: ((connected: boolean) => void) | null = null

// Mock the gameSocket before imports.
vi.mock('@/api/socket', () => ({
  gameSocket: {
    on: (cb: (data: any) => void) => {
      messageCallback = cb
      return mockOn()
    },
    onStatusChange: (cb: (connected: boolean) => void) => {
      statusCallback = cb
      return mockOnStatusChange()
    },
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
    
    // Reset mocks and callbacks.
    vi.clearAllMocks()
    mockUiStore.selectedTarget = null
    mockOn.mockReturnValue(vi.fn())
    mockOnStatusChange.mockReturnValue(vi.fn())
    messageCallback = null
    statusCallback = null
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

    it('should not reinitialize if already initialized', () => {
      store.init()
      store.init()
      store.init()

      // connect should only be called once due to guard.
      expect(mockConnect).toHaveBeenCalledTimes(1)
    })

    it('should setup status change listener', () => {
      store.init()

      expect(mockOnStatusChange).toHaveBeenCalled()
    })

    it('should setup message listener', () => {
      store.init()

      expect(mockOn).toHaveBeenCalled()
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

  describe('message handling', () => {
    it('should call worldStore.handleTick on tick message', () => {
      store.init()

      const tickPayload = {
        type: 'tick',
        year: 100,
        month: 5,
        avatars: [],
        events: [],
      }

      messageCallback?.(tickPayload)

      expect(mockWorldStore.handleTick).toHaveBeenCalledWith(tickPayload)
    })

    it('should refresh detail on tick if target is selected', () => {
      store.init()
      mockUiStore.selectedTarget = { type: 'avatar', id: 'a1' }

      messageCallback?.({ type: 'tick', year: 100, month: 5, avatars: [], events: [] })

      expect(mockUiStore.refreshDetail).toHaveBeenCalled()
    })

    it('should not refresh detail on tick if no target selected', () => {
      store.init()
      mockUiStore.selectedTarget = null

      messageCallback?.({ type: 'tick', year: 100, month: 5, avatars: [], events: [] })

      expect(mockUiStore.refreshDetail).not.toHaveBeenCalled()
    })

    it('should call worldStore.initialize on game_reinitialized message', () => {
      store.init()

      messageCallback?.({ type: 'game_reinitialized', message: 'Game reinitialized' })

      expect(mockWorldStore.initialize).toHaveBeenCalled()
    })

    it('should call __openLLMConfig on llm_config_required message', () => {
      const mockOpenLLMConfig = vi.fn()
      ;(window as any).__openLLMConfig = mockOpenLLMConfig
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      store.init()
      messageCallback?.({ type: 'llm_config_required', error: 'LLM not configured' })

      expect(mockOpenLLMConfig).toHaveBeenCalled()
      expect(consoleSpy).toHaveBeenCalled()

      consoleSpy.mockRestore()
      delete (window as any).__openLLMConfig
    })

    it('should handle llm_config_required when __openLLMConfig is not defined', () => {
      delete (window as any).__openLLMConfig
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      store.init()
      // Should not throw.
      messageCallback?.({ type: 'llm_config_required', error: 'LLM error' })

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })

    it('should ignore unknown message types', () => {
      store.init()

      // Should not throw.
      messageCallback?.({ type: 'unknown_type', data: 'something' })

      expect(mockWorldStore.handleTick).not.toHaveBeenCalled()
      expect(mockWorldStore.initialize).not.toHaveBeenCalled()
    })
  })

  describe('status change handling', () => {
    it('should update isConnected when status changes to connected', () => {
      store.init()

      statusCallback?.(true)

      expect(store.isConnected).toBe(true)
    })

    it('should update isConnected when status changes to disconnected', () => {
      store.init()
      statusCallback?.(true)

      statusCallback?.(false)

      expect(store.isConnected).toBe(false)
    })

    it('should clear lastError when connected', () => {
      store.init()
      // Simulate having an error.
      store.lastError = 'Some error'

      statusCallback?.(true)

      expect(store.lastError).toBeNull()
    })
  })
})
