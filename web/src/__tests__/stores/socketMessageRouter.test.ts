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
    applyAvatarDelta: vi.fn(() => true),
    initialize: vi.fn().mockResolvedValue(undefined),
  }
  const uiStore = {
    selectedTarget: null as null | { type: string; id: string },
    refreshDetail: vi.fn(),
    clearSelection: vi.fn(),
    openSystemMenu: vi.fn(),
    setLlmConfigError: vi.fn(),
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
    expect(uiStore.setLlmConfigError).toHaveBeenCalledWith('LLM required')
    expect(mockMessage.error).toHaveBeenCalledWith('LLM required')
  })

  it('applies an immediate avatar delta and refreshes the selected detail', () => {
    uiStore.selectedTarget = { type: 'avatar', id: 'a1' }
    routeSocketMessage(
      { type: 'avatar_delta', avatars: [{ id: 'a2', name: 'New' }], removed_avatar_ids: [], world_revision: 5 },
      { worldStore: worldStore as any, uiStore: uiStore as any },
    )

    expect(worldStore.applyAvatarDelta).toHaveBeenCalledWith(expect.objectContaining({ world_revision: 5 }), {
      directoryChanged: true,
    })
    expect(uiStore.refreshDetail).toHaveBeenCalled()
  })

  it('clears a selected avatar when an immediate delta removes it', () => {
    uiStore.selectedTarget = { type: 'avatar', id: 'a1' }
    routeSocketMessage(
      { type: 'avatar_delta', avatars: [], removed_avatar_ids: ['a1'], world_revision: 6 },
      { worldStore: worldStore as any, uiStore: uiStore as any },
    )

    expect(uiStore.clearSelection).toHaveBeenCalled()
    expect(uiStore.refreshDetail).not.toHaveBeenCalled()
  })

  it('shows toast without switching frontend locale', () => {
    routeSocketMessage(
      { type: 'toast', level: 'info', message: 'ok', language: 'en-US' },
      { worldStore: worldStore as any, uiStore: uiStore as any }
    )

    expect(mockMessage.info).toHaveBeenCalledWith('ok')
  })
})

