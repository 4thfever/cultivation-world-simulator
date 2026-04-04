import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const { mockFetchStatus, mockMessageSuccess, mockMessageWarning, mockMessageError } = vi.hoisted(() => ({
  mockFetchStatus: vi.fn(),
  mockMessageSuccess: vi.fn(),
  mockMessageWarning: vi.fn(),
  mockMessageError: vi.fn(),
}))

vi.mock('@/api', () => ({
  llmApi: {
    fetchStatus: mockFetchStatus,
  },
}))

vi.mock('@/utils/discreteApi', () => ({
  message: {
    success: mockMessageSuccess,
    warning: mockMessageWarning,
    error: mockMessageError,
  },
}))

import { useSystemMenuFlow } from '@/composables/useSystemMenuFlow'

describe('useSystemMenuFlow', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('opens game menu in game context', () => {
    const flow = useSystemMenuFlow()

    flow.openGameMenu()

    expect(flow.showMenu.value).toBe(true)
    expect(flow.menuDefaultTab.value).toBe('load')
    expect(flow.menuContext.value).toBe('game')
  })

  it('opens splash menu in splash context', () => {
    const flow = useSystemMenuFlow()

    flow.openSplashMenu('settings')

    expect(flow.showMenu.value).toBe(true)
    expect(flow.menuDefaultTab.value).toBe('settings')
    expect(flow.menuContext.value).toBe('splash')
  })

  it('routes startup to llm tab when llm is missing', async () => {
    mockFetchStatus.mockResolvedValue({ configured: false })
    const flow = useSystemMenuFlow()

    await flow.performStartupCheck('splash')

    expect(flow.showMenu.value).toBe(true)
    expect(flow.menuDefaultTab.value).toBe('llm')
    expect(flow.canCloseMenu.value).toBe(false)
    expect(flow.menuContext.value).toBe('splash')
    expect(mockMessageWarning).toHaveBeenCalled()
  })

  it('handles llm ready by reopening start path', () => {
    const flow = useSystemMenuFlow()
    flow.openLLMConfig('game')

    flow.handleLLMReady()

    expect(flow.canCloseMenu.value).toBe(true)
    expect(flow.menuDefaultTab.value).toBe('start')
    expect(mockMessageSuccess).toHaveBeenCalled()
  })

  it('shows llm error fallback on status fetch failure', async () => {
    mockFetchStatus.mockRejectedValue(new Error('network'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const flow = useSystemMenuFlow()

    await flow.performStartupCheck('game')

    expect(flow.menuDefaultTab.value).toBe('llm')
    expect(flow.canCloseMenu.value).toBe(false)
    expect(mockMessageError).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })
})
