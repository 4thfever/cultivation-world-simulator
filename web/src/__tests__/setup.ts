import { vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

// Use fake timers globally for consistent async testing.
vi.useFakeTimers()

// Setup fresh Pinia instance for each test.
beforeEach(() => {
  setActivePinia(createPinia())
})

// Cleanup after each test.
afterEach(() => {
  vi.clearAllMocks()
})
