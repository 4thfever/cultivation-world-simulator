import { beforeEach, describe, expect, it, vi } from 'vitest'

const getMock = vi.fn()
const postMock = vi.fn()
const deleteMock = vi.fn()

vi.mock('@/api/http', () => ({
  httpClient: {
    get: getMock,
    post: postMock,
    delete: deleteMock,
  },
}))

describe('public api module migration', () => {
  beforeEach(() => {
    getMock.mockReset()
    postMock.mockReset()
    deleteMock.mockReset()
  })

  it('worldApi fetches world state and map from /api/v1', async () => {
    const { worldApi } = await import('@/api/modules/world')
    getMock.mockResolvedValueOnce({ status: 'ok', year: 100, month: 1 })
    getMock.mockResolvedValueOnce({ data: [], regions: [], render_config: {} })

    const state = await worldApi.fetchInitialState()
    const map = await worldApi.fetchMap()

    expect(getMock).toHaveBeenNthCalledWith(1, '/api/v1/query/world/state')
    expect(getMock).toHaveBeenNthCalledWith(2, '/api/v1/query/world/map')
    expect(state.avatars).toEqual([])
    expect(state.events).toEqual([])
    expect(map.renderConfig).toEqual({ water_speed: 'high', cloud_frequency: 'none' })
  })

  it('eventApi fetches events from /api/v1 query endpoint', async () => {
    const { eventApi } = await import('@/api/modules/event')
    getMock.mockResolvedValue({ events: [], next_cursor: null, has_more: false })

    const page = await eventApi.fetchEvents({ avatar_id: 'a1', limit: 20 })

    expect(getMock).toHaveBeenCalledWith('/api/v1/query/events?avatar_id=a1&limit=20')
    expect(page).toEqual({ events: [], nextCursor: null, hasMore: false })
  })

  it('eventApi cleans up events through /api/v1 command endpoint', async () => {
    const { eventApi } = await import('@/api/modules/event')
    deleteMock.mockResolvedValue({ deleted: 12 })

    await eventApi.cleanupEvents(false, 1200)

    expect(deleteMock).toHaveBeenCalledWith('/api/v1/command/events/cleanup?keep_major=false&before_month_stamp=1200')
  })

  it('worldApi fetches sect territories from /api/v1', async () => {
    const { worldApi } = await import('@/api/modules/world')
    getMock.mockResolvedValue({ sects: [] })

    await worldApi.fetchSectTerritories()

    expect(getMock).toHaveBeenCalledWith('/api/v1/query/sects/territories')
  })

  it('systemApi uses /api/v1 lifecycle and save endpoints', async () => {
    const { systemApi } = await import('@/api/modules/system')
    getMock.mockResolvedValue({ status: 'idle' })
    postMock.mockResolvedValue({ status: 'ok' })

    await systemApi.fetchInitStatus()
    await systemApi.fetchSaves()
    await systemApi.saveGame('存档A')
    await systemApi.loadGame('save.json')

    expect(getMock).toHaveBeenNthCalledWith(1, '/api/v1/query/runtime/status')
    expect(getMock).toHaveBeenNthCalledWith(2, '/api/v1/query/saves')
    expect(postMock).toHaveBeenNthCalledWith(1, '/api/v1/command/game/save', { custom_name: '存档A' })
    expect(postMock).toHaveBeenNthCalledWith(2, '/api/v1/command/game/load', { filename: 'save.json' })
  })

  it('systemApi startNewGame and shutdown use /api/v1 endpoints', async () => {
    const { systemApi } = await import('@/api/modules/system')
    postMock.mockResolvedValue({ status: 'ok' })

    await systemApi.startNewGame()
    await systemApi.shutdown()

    expect(postMock).toHaveBeenNthCalledWith(1, '/api/v1/command/game/reinit', {})
    expect(postMock).toHaveBeenNthCalledWith(2, '/api/v1/command/system/shutdown', {})
  })
})
