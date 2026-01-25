import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, ref, nextTick } from 'vue'
import { useUiStore } from '@/stores/ui'
import { useSystemStore } from '@/stores/system'

// Use vi.hoisted to define mocks before vi.mock is hoisted.
const { mockFetchStatus, mockFetchConfig, mockTestConnection, mockMessageSuccess, mockMessageWarning, mockMessageError } = vi.hoisted(() => ({
  mockFetchStatus: vi.fn(),
  mockFetchConfig: vi.fn(),
  mockTestConnection: vi.fn(),
  mockMessageSuccess: vi.fn(),
  mockMessageWarning: vi.fn(),
  mockMessageError: vi.fn(),
}))

// Mock the API module.
vi.mock('@/api', () => ({
  llmApi: {
    fetchStatus: mockFetchStatus,
    fetchConfig: mockFetchConfig,
    testConnection: mockTestConnection,
  },
}))

// Mock the discreteApi.
vi.mock('@/utils/discreteApi', () => ({
  message: {
    success: mockMessageSuccess,
    warning: mockMessageWarning,
    error: mockMessageError,
  },
}))

import { useGameControl } from '@/composables/useGameControl'

// Helper to create test component.
const createTestComponent = (gameInitialized = ref(false)) => {
  return defineComponent({
    setup() {
      const result = useGameControl(gameInitialized)
      return { ...result }
    },
    template: '<div></div>'
  })
}

describe('useGameControl', () => {
  let uiStore: ReturnType<typeof useUiStore>
  let systemStore: ReturnType<typeof useSystemStore>

  beforeEach(() => {
    uiStore = useUiStore()
    systemStore = useSystemStore()
    vi.clearAllMocks()
  })

  afterEach(() => {
    // Clean up global function.
    delete (window as any).__openLLMConfig
  })

  describe('initial state', () => {
    it('should have correct initial values', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      expect(wrapper.vm.showMenu).toBe(false)
      expect(wrapper.vm.menuDefaultTab).toBe('load')
      expect(wrapper.vm.canCloseMenu).toBe(true)

      wrapper.unmount()
    })

    it('should expose openLLMConfig to window on mount', async () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)
      await nextTick()

      expect((window as any).__openLLMConfig).toBeDefined()
      expect(typeof (window as any).__openLLMConfig).toBe('function')

      wrapper.unmount()
    })
  })

  describe('handleKeydown', () => {
    it('should clear selection when Escape pressed and target selected', () => {
      const TestComponent = createTestComponent(ref(true))
      const wrapper = mount(TestComponent)

      uiStore.selectedTarget = { type: 'avatar', id: '123' }

      wrapper.vm.handleKeydown(new KeyboardEvent('keydown', { key: 'Escape' }))

      expect(uiStore.selectedTarget).toBeNull()
      wrapper.unmount()
    })

    it('should open menu when Escape pressed and no selection', () => {
      const TestComponent = createTestComponent(ref(true))
      const wrapper = mount(TestComponent)

      uiStore.selectedTarget = null
      wrapper.vm.showMenu = false

      wrapper.vm.handleKeydown(new KeyboardEvent('keydown', { key: 'Escape' }))

      expect(wrapper.vm.showMenu).toBe(true)
      expect(wrapper.vm.menuDefaultTab).toBe('load')
      wrapper.unmount()
    })

    it('should close menu when Escape pressed and menu open and closable', () => {
      const TestComponent = createTestComponent(ref(true))
      const wrapper = mount(TestComponent)

      uiStore.selectedTarget = null
      wrapper.vm.showMenu = true
      wrapper.vm.canCloseMenu = true

      wrapper.vm.handleKeydown(new KeyboardEvent('keydown', { key: 'Escape' }))

      expect(wrapper.vm.showMenu).toBe(false)
      wrapper.unmount()
    })

    it('should not close menu when Escape pressed but menu not closable', () => {
      const TestComponent = createTestComponent(ref(true))
      const wrapper = mount(TestComponent)

      uiStore.selectedTarget = null
      wrapper.vm.showMenu = true
      wrapper.vm.canCloseMenu = false

      wrapper.vm.handleKeydown(new KeyboardEvent('keydown', { key: 'Escape' }))

      expect(wrapper.vm.showMenu).toBe(true)
      wrapper.unmount()
    })

    it('should ignore non-Escape keys', () => {
      const TestComponent = createTestComponent(ref(true))
      const wrapper = mount(TestComponent)

      wrapper.vm.showMenu = false

      wrapper.vm.handleKeydown(new KeyboardEvent('keydown', { key: 'Enter' }))

      expect(wrapper.vm.showMenu).toBe(false)
      wrapper.unmount()
    })
  })

  describe('performStartupCheck', () => {
    it('should open menu with start tab when LLM configured and connected', async () => {
      mockFetchStatus.mockResolvedValue({ configured: true })
      mockFetchConfig.mockResolvedValue({ provider: 'openai', model: 'gpt-4' })
      mockTestConnection.mockResolvedValue(undefined)

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await wrapper.vm.performStartupCheck()

      expect(wrapper.vm.showMenu).toBe(true)
      expect(wrapper.vm.menuDefaultTab).toBe('start')
      expect(wrapper.vm.canCloseMenu).toBe(true)
      wrapper.unmount()
    })

    it('should force LLM config when not configured', async () => {
      mockFetchStatus.mockResolvedValue({ configured: false })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await wrapper.vm.performStartupCheck()

      expect(wrapper.vm.showMenu).toBe(true)
      expect(wrapper.vm.menuDefaultTab).toBe('llm')
      expect(wrapper.vm.canCloseMenu).toBe(false)
      expect(mockMessageWarning).toHaveBeenCalledWith('检测到 LLM 未配置，请先完成设置')
      wrapper.unmount()
    })

    it('should force LLM config when connection test fails', async () => {
      mockFetchStatus.mockResolvedValue({ configured: true })
      mockFetchConfig.mockResolvedValue({ provider: 'openai', model: 'gpt-4' })
      mockTestConnection.mockRejectedValue(new Error('Connection failed'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await wrapper.vm.performStartupCheck()

      expect(wrapper.vm.showMenu).toBe(true)
      expect(wrapper.vm.menuDefaultTab).toBe('llm')
      expect(wrapper.vm.canCloseMenu).toBe(false)
      expect(mockMessageError).toHaveBeenCalledWith('LLM 连接测试失败，请重新配置')

      consoleSpy.mockRestore()
      wrapper.unmount()
    })

    it('should handle status fetch error', async () => {
      mockFetchStatus.mockRejectedValue(new Error('Network error'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      await wrapper.vm.performStartupCheck()

      expect(wrapper.vm.menuDefaultTab).toBe('llm')
      expect(wrapper.vm.canCloseMenu).toBe(false)
      expect(mockMessageError).toHaveBeenCalledWith('无法获取系统状态')

      consoleSpy.mockRestore()
      wrapper.unmount()
    })
  })

  describe('handleLLMReady', () => {
    it('should enable menu close and show success message', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      wrapper.vm.canCloseMenu = false

      wrapper.vm.handleLLMReady()

      expect(wrapper.vm.canCloseMenu).toBe(true)
      expect(wrapper.vm.menuDefaultTab).toBe('start')
      expect(mockMessageSuccess).toHaveBeenCalledWith('LLM 配置成功，请开始游戏')
      wrapper.unmount()
    })
  })

  describe('handleMenuClose', () => {
    it('should close menu when closable', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      wrapper.vm.showMenu = true
      wrapper.vm.canCloseMenu = true

      wrapper.vm.handleMenuClose()

      expect(wrapper.vm.showMenu).toBe(false)
      wrapper.unmount()
    })

    it('should not close menu when not closable', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      wrapper.vm.showMenu = true
      wrapper.vm.canCloseMenu = false

      wrapper.vm.handleMenuClose()

      expect(wrapper.vm.showMenu).toBe(true)
      wrapper.unmount()
    })
  })

  describe('toggleManualPause', () => {
    it('should call systemStore.togglePause', () => {
      const togglePauseSpy = vi.spyOn(systemStore, 'togglePause').mockResolvedValue(undefined)

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      wrapper.vm.toggleManualPause()

      expect(togglePauseSpy).toHaveBeenCalled()
      wrapper.unmount()
    })
  })

  describe('openLLMConfig', () => {
    it('should open menu with llm tab', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      wrapper.vm.showMenu = false

      wrapper.vm.openLLMConfig()

      expect(wrapper.vm.menuDefaultTab).toBe('llm')
      expect(wrapper.vm.showMenu).toBe(true)
      wrapper.unmount()
    })
  })
})
