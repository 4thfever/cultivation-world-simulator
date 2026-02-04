import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Use vi.hoisted to define mocks before vi.mock is hoisted.
const {
  mockOn,
  mockOnStatusChange,
  mockConnect,
  mockDisconnect,
  mockWorldStore,
  mockUiStore,
  mockMessage,
} = vi.hoisted(() => ({
  mockOn: vi.fn(() => vi.fn()),
  mockOnStatusChange: vi.fn(() => vi.fn()),
  mockConnect: vi.fn(),
  mockDisconnect: vi.fn(),
  mockWorldStore: {
    handleTick: vi.fn(),
    initialize: vi.fn().mockResolvedValue(undefined),
  },
  mockUiStore: {
    selectedTarget: null as { type: string; id: string } | null,
    refreshDetail: vi.fn(),
  },
  mockMessage: {
    error: vi.fn(),
    warning: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}))

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

vi.mock('@/utils/discreteApi', () => ({
  message: mockMessage,
}))

// Mock i18n with mutable module-level variables.
let mockI18nMode = 'composition'
let mockI18nLocale: any = { value: 'zh-CN' }

vi.mock('@/locales', () => ({
  default: {
    get mode() { return mockI18nMode },
    global: {
      get locale() { return mockI18nLocale },
      set locale(val) { mockI18nLocale = val },
    },
  },
}))

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

    // Reset i18n mock.
    mockI18nMode = 'composition'
    mockI18nLocale = { value: 'zh-CN' }
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

  describe('toast message handling', () => {
    it('should show error toast for error level', () => {
      store.init()

      messageCallback?.({ type: 'toast', level: 'error', message: 'Error message' })

      expect(mockMessage.error).toHaveBeenCalledWith('Error message')
    })

    it('should show warning toast for warning level', () => {
      store.init()

      messageCallback?.({ type: 'toast', level: 'warning', message: 'Warning message' })

      expect(mockMessage.warning).toHaveBeenCalledWith('Warning message')
    })

    it('should show success toast for success level', () => {
      store.init()

      messageCallback?.({ type: 'toast', level: 'success', message: 'Success message' })

      expect(mockMessage.success).toHaveBeenCalledWith('Success message')
    })

    it('should show info toast for info level', () => {
      store.init()

      messageCallback?.({ type: 'toast', level: 'info', message: 'Info message' })

      expect(mockMessage.info).toHaveBeenCalledWith('Info message')
    })

    it('should show info toast for unknown level', () => {
      store.init()

      messageCallback?.({ type: 'toast', level: 'unknown', message: 'Unknown level message' })

      expect(mockMessage.info).toHaveBeenCalledWith('Unknown level message')
    })

    it('should switch language in composition mode when language field is present', () => {
      mockI18nMode = 'composition'
      mockI18nLocale = { value: 'zh-CN' }
      const localStorageSpy = vi.spyOn(Storage.prototype, 'setItem')

      store.init()
      messageCallback?.({ type: 'toast', level: 'info', message: 'Test', language: 'en-US' })

      expect(mockI18nLocale.value).toBe('en-US')
      expect(localStorageSpy).toHaveBeenCalledWith('app_locale', 'en-US')
      localStorageSpy.mockRestore()
    })

    it('should switch language in legacy mode when language field is present', () => {
      mockI18nMode = 'legacy'
      mockI18nLocale = 'zh-CN'
      const localStorageSpy = vi.spyOn(Storage.prototype, 'setItem')

      store.init()
      messageCallback?.({ type: 'toast', level: 'info', message: 'Test', language: 'en-US' })

      expect(mockI18nLocale).toBe('en-US')
      expect(localStorageSpy).toHaveBeenCalledWith('app_locale', 'en-US')
      localStorageSpy.mockRestore()
    })

    it('should not switch language if same as current', () => {
      mockI18nMode = 'composition'
      mockI18nLocale = { value: 'en-US' }
      const localStorageSpy = vi.spyOn(Storage.prototype, 'setItem')

      store.init()
      messageCallback?.({ type: 'toast', level: 'info', message: 'Test', language: 'en-US' })

      // Should not call setItem if language is same.
      expect(localStorageSpy).not.toHaveBeenCalled()
      localStorageSpy.mockRestore()
    })

    it('should update document.documentElement.lang for zh-CN', () => {
      mockI18nMode = 'composition'
      mockI18nLocale = { value: 'en-US' }

      store.init()
      messageCallback?.({ type: 'toast', level: 'info', message: 'Test', language: 'zh-CN' })

      expect(document.documentElement.lang).toBe('zh-CN')
    })

    it('should update document.documentElement.lang for en-US', () => {
      mockI18nMode = 'composition'
      mockI18nLocale = { value: 'zh-CN' }

      store.init()
      messageCallback?.({ type: 'toast', level: 'info', message: 'Test', language: 'en-US' })

      expect(document.documentElement.lang).toBe('en')
    })

    it('should handle language switch errors gracefully', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      // Create a getter that throws.
      mockI18nMode = 'composition'
      const errorObj = {
        get value() { throw new Error('Test error') },
        set value(_v) { throw new Error('Test error') },
      }
      mockI18nLocale = errorObj

      store.init()
      // Should not throw.
      messageCallback?.({ type: 'toast', level: 'info', message: 'Test', language: 'en-US' })

      expect(consoleSpy).toHaveBeenCalledWith('[Socket] Failed to switch language:', expect.any(Error))
      consoleSpy.mockRestore()
    })
  })

  describe('llm_config_required alert handling', () => {
    it('should call alert after timeout for llm_config_required', async () => {
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      store.init()
      messageCallback?.({ type: 'llm_config_required', error: 'LLM error' })

      // Run the setTimeout.
      await vi.advanceTimersByTimeAsync(500)

      expect(alertSpy).toHaveBeenCalled()
      alertSpy.mockRestore()
      consoleSpy.mockRestore()
    })

    it('should use default message when error is not provided', async () => {
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      store.init()
      messageCallback?.({ type: 'llm_config_required' })

      await vi.advanceTimersByTimeAsync(500)

      expect(alertSpy).toHaveBeenCalledWith(expect.stringContaining('LLM 连接失败'))
      alertSpy.mockRestore()
      consoleSpy.mockRestore()
    })
  })

  describe('game_reinitialized alert handling', () => {
    it('should call alert after timeout for game_reinitialized', async () => {
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

      store.init()
      messageCallback?.({ type: 'game_reinitialized', message: 'Game restarted' })

      await vi.advanceTimersByTimeAsync(300)

      expect(alertSpy).toHaveBeenCalledWith('Game restarted')
      alertSpy.mockRestore()
      consoleSpy.mockRestore()
    })

    it('should use default message when message is not provided', async () => {
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

      store.init()
      messageCallback?.({ type: 'game_reinitialized' })

      await vi.advanceTimersByTimeAsync(300)

      expect(alertSpy).toHaveBeenCalledWith('LLM 配置成功，游戏已重新初始化')
      alertSpy.mockRestore()
      consoleSpy.mockRestore()
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
