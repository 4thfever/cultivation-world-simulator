import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'

// Use vi.hoisted to define mocks before vi.mock is hoisted.
const { mockAdd, mockRemove, mockStart, mockStop, mockTickerCallbacks, resetMockState } = vi.hoisted(() => {
  const callbacks: Set<(ticker: any) => void> = new Set()
  let started = false

  return {
    mockTickerCallbacks: callbacks,
    mockAdd: vi.fn((cb) => { callbacks.add(cb) }),
    mockRemove: vi.fn((cb) => { callbacks.delete(cb) }),
    mockStart: vi.fn(() => { started = true }),
    mockStop: vi.fn(() => { started = false }),
    resetMockState: () => {
      callbacks.clear()
      started = false
    }
  }
})

// Mock pixi.js Ticker.
vi.mock('pixi.js', () => ({
  Ticker: vi.fn().mockImplementation(() => ({
    add: mockAdd,
    remove: mockRemove,
    start: mockStart,
    stop: mockStop,
    get started() { return false },
    deltaTime: 16.67,
  })),
}))

// Import after mocking.
import { useSharedTicker } from '@/components/game/composables/useSharedTicker'

// Create a test component that uses the composable.
const createTestComponent = (callback: (delta: number) => void) => {
  return defineComponent({
    setup() {
      useSharedTicker(callback)
      return {}
    },
    template: '<div></div>'
  })
}

describe('useSharedTicker', () => {
  beforeEach(() => {
    resetMockState()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('lifecycle', () => {
    it('should add callback on mount', async () => {
      const callback = vi.fn()
      const TestComponent = createTestComponent(callback)

      const wrapper = mount(TestComponent)
      await nextTick()

      expect(mockAdd).toHaveBeenCalled()
      wrapper.unmount()
    })

    it('should start ticker on first consumer mount', async () => {
      const callback = vi.fn()
      const TestComponent = createTestComponent(callback)

      const wrapper = mount(TestComponent)
      await nextTick()

      expect(mockStart).toHaveBeenCalled()
      wrapper.unmount()
    })

    it('should remove callback on unmount', async () => {
      const callback = vi.fn()
      const TestComponent = createTestComponent(callback)

      const wrapper = mount(TestComponent)
      await nextTick()

      wrapper.unmount()
      await nextTick()

      expect(mockRemove).toHaveBeenCalled()
    })

    it('should stop ticker when last consumer unmounts', async () => {
      const callback = vi.fn()
      const TestComponent = createTestComponent(callback)

      const wrapper = mount(TestComponent)
      await nextTick()

      wrapper.unmount()
      await nextTick()

      expect(mockStop).toHaveBeenCalled()
    })
  })

  describe('multiple consumers', () => {
    it('should handle multiple consumers', async () => {
      const callback1 = vi.fn()
      const callback2 = vi.fn()
      const TestComponent1 = createTestComponent(callback1)
      const TestComponent2 = createTestComponent(callback2)

      const wrapper1 = mount(TestComponent1)
      await nextTick()

      const wrapper2 = mount(TestComponent2)
      await nextTick()

      // Both callbacks should be added.
      expect(mockAdd).toHaveBeenCalledTimes(2)

      // Unmount first consumer.
      wrapper1.unmount()
      await nextTick()

      // Ticker should still have one consumer.
      expect(mockTickerCallbacks.size).toBe(1)

      // Unmount second consumer.
      wrapper2.unmount()
      await nextTick()

      // Now ticker should stop.
      expect(mockStop).toHaveBeenCalled()
    })
  })

  describe('callback invocation', () => {
    it('should pass delta time to callback when ticker fires', async () => {
      const callback = vi.fn()
      const TestComponent = createTestComponent(callback)

      const wrapper = mount(TestComponent)
      await nextTick()

      // Simulate a tick by calling all registered callbacks.
      mockTickerCallbacks.forEach(cb => cb({ deltaTime: 16.67 }))

      expect(callback).toHaveBeenCalledWith(16.67)
      wrapper.unmount()
    })
  })
})
