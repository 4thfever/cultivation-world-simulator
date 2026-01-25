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
})
