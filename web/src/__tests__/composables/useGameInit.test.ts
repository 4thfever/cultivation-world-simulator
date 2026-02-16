import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'
import { useSystemStore } from '@/stores/system'
import { useWorldStore } from '@/stores/world'
import { useSocketStore } from '@/stores/socket'
import type { InitStatusDTO } from '@/types/api'

// Use vi.hoisted to define mocks before vi.mock is hoisted.
const { mockLoadBaseTextures } = vi.hoisted(() => ({
  mockLoadBaseTextures: vi.fn().mockResolvedValue(undefined),
}))

// Mock useTextures composable.
vi.mock('@/components/game/composables/useTextures', () => ({
  useTextures: () => ({
    loadBaseTextures: mockLoadBaseTextures,
  }),
}))

// Mock API modules to prevent network requests.
vi.mock('@/api', () => ({
  worldApi: {
    fetchMap: vi.fn().mockResolvedValue({
      data: [[{ type: 'grass' }]],
      regions: [],
      config: {},
    }),
    fetchInitialState: vi.fn().mockResolvedValue({
      year: 0,
      month: 0,
      avatars: [],
    }),
  },
  systemApi: {
    fetchInitStatus: vi.fn(),
    setInitialized: vi.fn(),
  },
}))

import { useGameInit } from '@/composables/useGameInit'

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

// Helper to create test component.
const createTestComponent = (options: { onIdle?: () => void } = {}) => {
  return defineComponent({
    setup() {
      const result = useGameInit(options)
      return { ...result }
    },
    template: '<div></div>'
  })
}

describe('useGameInit', () => {
  let systemStore: ReturnType<typeof useSystemStore>
  let worldStore: ReturnType<typeof useWorldStore>
  let socketStore: ReturnType<typeof useSocketStore>

  beforeEach(() => {
    systemStore = useSystemStore()
    worldStore = useWorldStore()
    socketStore = useSocketStore()
    vi.clearAllMocks()
    // Ensure store actions are mocked to avoid side effects
    vi.spyOn(worldStore, 'preloadMap').mockResolvedValue(undefined)
    vi.spyOn(worldStore, 'preloadAvatars').mockResolvedValue(undefined)
    vi.spyOn(worldStore, 'initialize').mockResolvedValue(undefined)
    vi.spyOn(worldStore, 'reset')
    vi.spyOn(systemStore, 'setInitialized')
    vi.spyOn(socketStore, 'init')
    vi.spyOn(socketStore, 'disconnect')

    // Ensure systemStore.fetchInitStatus returns immediately.
    vi.spyOn(systemStore, 'fetchInitStatus').mockResolvedValue(createMockStatus())
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  describe('initial state', () => {
    it('should expose startPolling and stopPolling functions', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      expect(typeof wrapper.vm.startPolling).toBe('function')
      expect(typeof wrapper.vm.stopPolling).toBe('function')

      wrapper.unmount()
    })

    it('should expose initializeGame function', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      expect(typeof wrapper.vm.initializeGame).toBe('function')

      wrapper.unmount()
    })

    it('should expose initStatus ref from store', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      expect(wrapper.vm.initStatus).toBeDefined()

      wrapper.unmount()
    })

    it('should have mapPreloaded initially false', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      expect(wrapper.vm.mapPreloaded).toBe(false)

      wrapper.unmount()
    })

    it('should have avatarsPreloaded initially false', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      expect(wrapper.vm.avatarsPreloaded).toBe(false)

      wrapper.unmount()
    })
  })

  describe('lifecycle', () => {
    it('should disconnect socket on unmount', async () => {
      const disconnectSpy = vi.spyOn(socketStore, 'disconnect')

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)
      await nextTick()

      wrapper.unmount()

      expect(disconnectSpy).toHaveBeenCalled()
    })
  })

  describe('gameInitialized alias', () => {
    it('should expose gameInitialized as alias for isInitialized', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      expect(wrapper.vm.gameInitialized).toBeDefined()

      wrapper.unmount()
    })
  })

  describe('showLoading', () => {
    it('should expose showLoading from store', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      expect(wrapper.vm.showLoading).toBeDefined()

      wrapper.unmount()
    })
  })

  describe('pollInitStatus', () => {
    it('should call onIdle callback when status changes to idle', async () => {
      const onIdleMock = vi.fn()

      // First call returns non-idle, second call returns idle.
      vi.spyOn(systemStore, 'fetchInitStatus')
        .mockResolvedValueOnce(createMockStatus({ status: 'initializing' }))
        .mockResolvedValueOnce(createMockStatus({ status: 'idle' }))

      const TestComponent = createTestComponent({ onIdle: onIdleMock })
      const wrapper = mount(TestComponent)

      // First poll - initializing.
      await vi.advanceTimersByTimeAsync(0)
      await nextTick()

      // Second poll - idle.
      await vi.advanceTimersByTimeAsync(1000)
      await nextTick()

      expect(onIdleMock).toHaveBeenCalled()

      wrapper.unmount()
    })

    it('should reset world and system when returning to idle from initialized state', async () => {
      const resetSpy = vi.spyOn(worldStore, 'reset')
      const setInitializedSpy = vi.spyOn(systemStore, 'setInitialized')

      // Simulate already initialized.
      systemStore.setInitialized(true)

      vi.spyOn(systemStore, 'fetchInitStatus')
        .mockResolvedValue(createMockStatus({ status: 'idle' }))

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await vi.advanceTimersByTimeAsync(0)
      await nextTick()

      expect(setInitializedSpy).toHaveBeenCalledWith(false)
      expect(resetSpy).toHaveBeenCalled()

      wrapper.unmount()
    })

    it('should preload map when phase is in MAP_READY', async () => {
      const preloadMapSpy = vi.spyOn(worldStore, 'preloadMap')

      vi.spyOn(systemStore, 'fetchInitStatus')
        .mockResolvedValue(createMockStatus({
          status: 'initializing',
          phase_name: 'initializing_sects' // This is in MAP_READY.
        }))

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await vi.advanceTimersByTimeAsync(0)
      await nextTick()

      expect(preloadMapSpy).toHaveBeenCalled()
      expect(wrapper.vm.mapPreloaded).toBe(true)

      wrapper.unmount()
    })

    it('should not preload map twice', async () => {
      const preloadMapSpy = vi.spyOn(worldStore, 'preloadMap')

      vi.spyOn(systemStore, 'fetchInitStatus')
        .mockResolvedValue(createMockStatus({
          status: 'initializing',
          phase_name: 'initializing_sects'
        }))

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      // First poll.
      await vi.advanceTimersByTimeAsync(0)
      await nextTick()

      // Second poll.
      await vi.advanceTimersByTimeAsync(1000)
      await nextTick()

      // Should only be called once.
      expect(preloadMapSpy).toHaveBeenCalledTimes(1)

      wrapper.unmount()
    })

    it('should preload avatars when phase is in AVATAR_READY', async () => {
      const preloadAvatarsSpy = vi.spyOn(worldStore, 'preloadAvatars')

      vi.spyOn(systemStore, 'fetchInitStatus')
        .mockResolvedValue(createMockStatus({
          status: 'initializing',
          phase_name: 'checking_llm' // This is in AVATAR_READY.
        }))

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await vi.advanceTimersByTimeAsync(0)
      await nextTick()

      expect(preloadAvatarsSpy).toHaveBeenCalled()
      expect(wrapper.vm.avatarsPreloaded).toBe(true)

      wrapper.unmount()
    })

    it('should initialize game when status transitions to ready', async () => {
      const initializeSpy = vi.spyOn(worldStore, 'initialize').mockResolvedValue(undefined)
      const setInitializedSpy = vi.spyOn(systemStore, 'setInitialized')

      // First call returns initializing, second call returns ready.
      vi.spyOn(systemStore, 'fetchInitStatus')
        .mockResolvedValueOnce(createMockStatus({ status: 'initializing' }))
        .mockResolvedValueOnce(createMockStatus({ status: 'ready' }))

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      // First poll - initializing.
      await vi.advanceTimersByTimeAsync(0)
      await nextTick()

      // Second poll - ready.
      await vi.advanceTimersByTimeAsync(1000)
      await nextTick()

      expect(initializeSpy).toHaveBeenCalled()
      expect(setInitializedSpy).toHaveBeenCalledWith(true)
      expect(mockLoadBaseTextures).toHaveBeenCalled()

      wrapper.unmount()
    })

    it('should handle fetch error gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      vi.spyOn(systemStore, 'fetchInitStatus')
        .mockRejectedValue(new Error('Network error'))

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await vi.advanceTimersByTimeAsync(0)
      await nextTick()

      expect(consoleSpy).toHaveBeenCalledWith('Failed to fetch init status:', expect.any(Error))

      consoleSpy.mockRestore()
      wrapper.unmount()
    })

    it('should return early if fetchInitStatus returns null', async () => {
      const preloadMapSpy = vi.spyOn(worldStore, 'preloadMap')

      vi.spyOn(systemStore, 'fetchInitStatus')
        .mockResolvedValue(null as any)

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await vi.advanceTimersByTimeAsync(0)
      await nextTick()

      // Nothing should be called because res is null.
      expect(preloadMapSpy).not.toHaveBeenCalled()

      wrapper.unmount()
    })
  })

  describe('initializeGame', () => {
    it('should reset world when already initialized', async () => {
      const resetSpy = vi.spyOn(worldStore, 'reset')
      const initializeSpy = vi.spyOn(worldStore, 'initialize').mockResolvedValue(undefined)

      // Mark as initialized.
      systemStore.setInitialized(true)

      vi.spyOn(systemStore, 'fetchInitStatus')
        .mockResolvedValue(createMockStatus({ status: 'idle' }))

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await vi.advanceTimersByTimeAsync(0)
      await nextTick()

      // Manually call initializeGame.
      await wrapper.vm.initializeGame()

      expect(resetSpy).toHaveBeenCalled()
      expect(initializeSpy).toHaveBeenCalled()

      wrapper.unmount()
    })

    it('should init socket if not connected', async () => {
      const initSpy = vi.spyOn(socketStore, 'init')
      const initializeSpy = vi.spyOn(worldStore, 'initialize').mockResolvedValue(undefined)

      vi.spyOn(systemStore, 'fetchInitStatus')
        .mockResolvedValue(createMockStatus({ status: 'idle' }))

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await vi.advanceTimersByTimeAsync(0)
      await nextTick()

      // Ensure socket is not connected.
      expect(socketStore.isConnected).toBe(false)

      await wrapper.vm.initializeGame()

      expect(initSpy).toHaveBeenCalled()

      wrapper.unmount()
    })
  })

  describe('stopPolling', () => {
    it('should clear interval when called', async () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await vi.advanceTimersByTimeAsync(0)
      await nextTick()

      // Stop polling.
      wrapper.vm.stopPolling()

      // Verify no more polls happen.
      vi.clearAllMocks()
      await vi.advanceTimersByTimeAsync(2000)

      expect(systemStore.fetchInitStatus).not.toHaveBeenCalled()

      wrapper.unmount()
    })
  })
})
