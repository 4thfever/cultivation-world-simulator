import { describe, it, expect, vi, beforeEach } from 'vitest'
import { routeSocketMessage } from '@/stores/socketMessageRouter'

const { mockMessage } = vi.hoisted(() => ({
  mockMessage: {
    error: vi.fn(),
    warning: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}))

vi.mock('@/utils/discreteApi', () => ({
  message: mockMessage,
}))

describe('socketMessageRouter', () => {
  const worldStore = {
    handleTick: vi.fn(),
    initialize: vi.fn().mockResolvedValue(undefined),
  }
  const uiStore = {
    selectedTarget: null as null | { type: string; id: string },
    refreshDetail: vi.fn(),
    openSystemMenu: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    uiStore.selectedTarget = null
  })

  it('routes tick message to world and refreshes selected detail', () => {
    uiStore.selectedTarget = { type: 'avatar', id: 'a1' }
    routeSocketMessage(
      { type: 'tick', year: 1, month: 1, events: [], avatars: [] },
      { worldStore: worldStore as any, uiStore: uiStore as any }
    )

    expect(worldStore.handleTick).toHaveBeenCalled()
    expect(uiStore.refreshDetail).toHaveBeenCalled()
  })

  it('opens llm config menu on llm_config_required', () => {
    routeSocketMessage(
      { type: 'llm_config_required', error: 'LLM required' },
      { worldStore: worldStore as any, uiStore: uiStore as any }
    )

    expect(uiStore.openSystemMenu).toHaveBeenCalledWith('llm', false)
    expect(mockMessage.error).toHaveBeenCalledWith('LLM required')
  })

  it('shows toast without switching frontend locale', () => {
    routeSocketMessage(
      { type: 'toast', level: 'info', message: 'ok', language: 'en-US' },
      { worldStore: worldStore as any, uiStore: uiStore as any }
    )

    expect(mockMessage.info).toHaveBeenCalledWith('ok')
  })
})

