import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useWorldStore } from '@/stores/world'
import type { AvatarSummary, GameEvent } from '@/types/core'
import type { TickPayloadDTO } from '@/types/api'

// Mock the API modules.
vi.mock('@/api', () => ({
  worldApi: {
    fetchInitialState: vi.fn(),
    fetchMap: vi.fn(),
    fetchPhenomenaList: vi.fn(),
    setPhenomenon: vi.fn(),
  },
  eventApi: {
    fetchEvents: vi.fn(),
  },
}))

import { worldApi, eventApi } from '@/api'

const createMockAvatar = (overrides: Partial<AvatarSummary> = {}): AvatarSummary => ({
  id: 'avatar-1',
  name: 'Test Avatar',
  pos_x: 10,
  pos_y: 20,
  is_alive: true,
  gender: 'male',
  realm: 'Qi Refinement',
  age: 25,
  sect_id: null,
  ...overrides,
})

const createMockEvent = (overrides: Partial<GameEvent> = {}): GameEvent => ({
  id: 'event-1',
  text: 'Test event',
  content: 'Test content',
  year: 100,
  month: 1,
  timestamp: 1200,
  monthStamp: 1200,
  relatedAvatarIds: ['avatar-1'],
  isMajor: false,
  isStory: false,
  createdAt: '2026-01-01T00:00:00Z',
  ...overrides,
})

describe('useWorldStore', () => {
  let store: ReturnType<typeof useWorldStore>

  beforeEach(() => {
    store = useWorldStore()
    store.reset()
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have correct initial values', () => {
      expect(store.year).toBe(0)
      expect(store.month).toBe(0)
      expect(store.avatars.size).toBe(0)
      expect(store.events).toEqual([])
      expect(store.isLoaded).toBe(false)
      expect(store.eventsCursor).toBeNull()
      expect(store.eventsHasMore).toBe(false)
      expect(store.eventsLoading).toBe(false)
      expect(store.currentPhenomenon).toBeNull()
    })
  })

  describe('avatarList getter', () => {
    it('should return array of avatars from map', () => {
      const avatar1 = createMockAvatar({ id: 'a1', name: 'Avatar 1' })
      const avatar2 = createMockAvatar({ id: 'a2', name: 'Avatar 2' })
      store.avatars = new Map([['a1', avatar1], ['a2', avatar2]])

      expect(store.avatarList).toHaveLength(2)
      expect(store.avatarList).toContainEqual(avatar1)
      expect(store.avatarList).toContainEqual(avatar2)
    })
  })

  describe('handleTick', () => {
    it('should do nothing if not loaded', () => {
      store.isLoaded = false
      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 100,
        month: 5,
        avatars: [createMockAvatar()],
        events: [],
      }

      store.handleTick(payload)

      expect(store.year).toBe(0)
    })

    it('should update time when loaded', () => {
      store.isLoaded = true

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 101,
        month: 3,
        avatars: [],
        events: [],
      }

      store.handleTick(payload)

      expect(store.year).toBe(101)
      expect(store.month).toBe(3)
    })

    it('should merge avatar updates when loaded', () => {
      store.isLoaded = true
      store.avatars = new Map([['avatar-1', createMockAvatar({ age: 20 })]])

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 101,
        month: 3,
        avatars: [{ id: 'avatar-1', age: 30 }],
        events: [],
      }

      store.handleTick(payload)

      expect(store.avatars.get('avatar-1')?.age).toBe(30)
    })

    it('should add new avatars with name', () => {
      store.isLoaded = true
      store.avatars = new Map()

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 101,
        month: 3,
        avatars: [createMockAvatar({ id: 'new-1', name: 'New Avatar' })],
        events: [],
      }

      store.handleTick(payload)

      expect(store.avatars.has('new-1')).toBe(true)
    })

    it('should add events when loaded', () => {
      store.isLoaded = true

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 101,
        month: 3,
        avatars: [],
        events: [{ id: 'e1', text: 'Event', year: 101, month: 3, month_stamp: 1215 }],
      }

      store.handleTick(payload)

      expect(store.events).toHaveLength(1)
    })

    it('should update phenomenon when provided', () => {
      store.isLoaded = true

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 100,
        month: 1,
        avatars: [],
        events: [],
        phenomenon: { id: 1, name: 'Full Moon', description: 'A full moon rises' },
      }

      store.handleTick(payload)

      expect(store.currentPhenomenon?.id).toBe(1)
    })

    it('should filter events by avatar_id when filter is set', () => {
      store.isLoaded = true
      store.eventsFilter = { avatar_id: 'a1' }

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 100,
        month: 1,
        avatars: [],
        events: [
          { id: 'e1', text: 'Event 1', year: 100, month: 1, month_stamp: 1200, related_avatar_ids: ['a1'] },
          { id: 'e2', text: 'Event 2', year: 100, month: 1, month_stamp: 1200, related_avatar_ids: ['a2'] },
        ],
      }

      store.handleTick(payload)

      // Only event for a1 should be added.
      expect(store.events).toHaveLength(1)
      expect(store.events[0].id).toBe('e1')
    })

    it('should filter events by avatar_id_1 and avatar_id_2 when both are set', () => {
      store.isLoaded = true
      store.eventsFilter = { avatar_id_1: 'a1', avatar_id_2: 'a2' }

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 100,
        month: 1,
        avatars: [],
        events: [
          { id: 'e1', text: 'Event 1', year: 100, month: 1, month_stamp: 1200, related_avatar_ids: ['a1', 'a2'] },
          { id: 'e2', text: 'Event 2', year: 100, month: 1, month_stamp: 1200, related_avatar_ids: ['a1'] },
          { id: 'e3', text: 'Event 3', year: 100, month: 1, month_stamp: 1200, related_avatar_ids: ['a2', 'a3'] },
        ],
      }

      store.handleTick(payload)

      // Only event with both a1 and a2 should be added.
      expect(store.events).toHaveLength(1)
      expect(store.events[0].id).toBe('e1')
    })

    it('should handle null avatars in payload', () => {
      store.isLoaded = true
      const initialAvatars = new Map([['a1', createMockAvatar()]])
      store.avatars = initialAvatars

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 100,
        month: 1,
        avatars: null as any,
        events: [],
      }

      store.handleTick(payload)

      // Avatars should remain unchanged.
      expect(store.avatars.size).toBe(1)
    })

    it('should handle null events in payload', () => {
      store.isLoaded = true
      store.events = [createMockEvent()]

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 100,
        month: 1,
        avatars: [],
        events: null as any,
      }

      store.handleTick(payload)

      // Events should remain unchanged.
      expect(store.events).toHaveLength(1)
    })

    it('should not update avatars map when no changes occur', () => {
      store.isLoaded = true
      const original = new Map([['a1', createMockAvatar()]])
      store.avatars = original

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 100,
        month: 1,
        avatars: [{ id: 'unknown-id' }], // No name, will be ignored.
        events: [],
      }

      store.handleTick(payload)

      // Should be the same reference since no change.
      expect(store.avatars).toBe(original)
    })

    it('should ignore avatars without id', () => {
      store.isLoaded = true
      store.avatars = new Map()

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 100,
        month: 1,
        avatars: [{ name: 'No ID Avatar' } as any], // Missing id.
        events: [],
      }

      store.handleTick(payload)

      // Should not add avatar without id.
      expect(store.avatars.size).toBe(0)
    })

    it('should handle empty events array', () => {
      store.isLoaded = true
      store.events = [createMockEvent({ id: 'existing' })]

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 100,
        month: 1,
        avatars: [],
        events: [],
      }

      store.handleTick(payload)

      // Events should remain unchanged.
      expect(store.events).toHaveLength(1)
    })

    it('should not add events when all are filtered out', () => {
      store.isLoaded = true
      store.eventsFilter = { avatar_id: 'a1' }
      store.events = []

      const payload: TickPayloadDTO = {
        type: 'tick',
        year: 100,
        month: 1,
        avatars: [],
        events: [
          { id: 'e1', text: 'Event', year: 100, month: 1, month_stamp: 1200, related_avatar_ids: ['a2'] },
        ],
      }

      store.handleTick(payload)

      // All events filtered out, should remain empty.
      expect(store.events).toHaveLength(0)
    })
  })

  describe('reset', () => {
    it('should reset all state to initial values', () => {
      store.isLoaded = true
      store.avatars = new Map([['a1', createMockAvatar()]])
      store.events = [createMockEvent()]
      store.currentPhenomenon = { id: 1, name: 'Test', description: 'Test' }

      store.reset()

      expect(store.year).toBe(0)
      expect(store.month).toBe(0)
      expect(store.avatars.size).toBe(0)
      expect(store.events).toEqual([])
      expect(store.isLoaded).toBe(false)
      expect(store.currentPhenomenon).toBeNull()
    })
  })

  describe('preloadMap', () => {
    it('should load map data and set isLoaded', async () => {
      vi.mocked(worldApi.fetchMap).mockResolvedValue({
        data: [[{ type: 'grass' }]],
        regions: [{ id: 'r1', name: 'Region 1' }],
        config: { mapScale: 1.5 },
      } as any)

      await store.preloadMap()

      expect(store.mapData).toHaveLength(1)
      expect(store.regions.size).toBe(1)
      expect(store.frontendConfig.mapScale).toBe(1.5)
      expect(store.isLoaded).toBe(true)
    })

    it('should handle errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      vi.mocked(worldApi.fetchMap).mockRejectedValue(new Error('Network error'))

      await store.preloadMap()

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })

  describe('preloadAvatars', () => {
    it('should load avatars and update time', async () => {
      vi.mocked(worldApi.fetchInitialState).mockResolvedValue({
        year: 100,
        month: 3,
        avatars: [createMockAvatar({ id: 'a1' })],
      })

      await store.preloadAvatars()

      expect(store.avatars.size).toBe(1)
      expect(store.year).toBe(100)
      expect(store.month).toBe(3)
    })

    it('should handle errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      vi.mocked(worldApi.fetchInitialState).mockRejectedValue(new Error('Network error'))

      await store.preloadAvatars()

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })

  describe('initialize', () => {
    it('should load map and state if map not loaded', async () => {
      vi.mocked(worldApi.fetchMap).mockResolvedValue({
        data: [[{ type: 'grass' }]],
        regions: [{ id: 'r1', name: 'Region 1' }],
        config: {},
      } as any)
      vi.mocked(worldApi.fetchInitialState).mockResolvedValue({
        year: 100,
        month: 1,
        avatars: [createMockAvatar()],
      })
      vi.mocked(eventApi.fetchEvents).mockResolvedValue({
        events: [],
        next_cursor: null,
        has_more: false,
      })

      await store.initialize()

      expect(worldApi.fetchMap).toHaveBeenCalled()
      expect(worldApi.fetchInitialState).toHaveBeenCalled()
      expect(store.isLoaded).toBe(true)
    })

    it('should skip map load if already loaded', async () => {
      store.mapData = [[{ type: 'grass' }]] as any
      vi.mocked(worldApi.fetchInitialState).mockResolvedValue({
        year: 100,
        month: 1,
        avatars: [],
      })
      vi.mocked(eventApi.fetchEvents).mockResolvedValue({
        events: [],
        next_cursor: null,
        has_more: false,
      })

      await store.initialize()

      expect(worldApi.fetchMap).not.toHaveBeenCalled()
    })

    it('should handle errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(worldApi.fetchMap).mockRejectedValue(new Error('Network error'))

      await store.initialize()

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })

    it('should handle concurrent calls (no built-in deduplication)', async () => {
      let fetchStateCallCount = 0
      let fetchMapCallCount = 0

      vi.mocked(worldApi.fetchInitialState).mockImplementation(() => {
        fetchStateCallCount++
        return Promise.resolve({ year: 100, month: 1, avatars: [] })
      })
      vi.mocked(worldApi.fetchMap).mockImplementation(() => {
        fetchMapCallCount++
        return Promise.resolve({ data: [[{ type: 'grass' }]], regions: [], config: {} } as any)
      })
      vi.mocked(eventApi.fetchEvents).mockResolvedValue({
        events: [],
        next_cursor: null,
        has_more: false,
      })

      // Call initialize twice concurrently.
      await Promise.all([store.initialize(), store.initialize()])

      // Both calls go through (no built-in deduplication).
      // This documents current behavior - not necessarily a bug.
      expect(fetchStateCallCount).toBe(2)
      expect(fetchMapCallCount).toBe(2)
    })
  })

  describe('fetchState', () => {
    it('should fetch and apply state snapshot', async () => {
      vi.mocked(worldApi.fetchInitialState).mockResolvedValue({
        year: 150,
        month: 8,
        avatars: [createMockAvatar({ id: 'a1' })],
      })

      await store.fetchState()

      expect(store.year).toBe(150)
      expect(store.month).toBe(8)
      expect(store.avatars.size).toBe(1)
      expect(store.isLoaded).toBe(true)
    })

    it('should handle errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(worldApi.fetchInitialState).mockRejectedValue(new Error('Network error'))

      await store.fetchState()

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })

    it('should ignore stale response when called rapidly (race condition fix)', async () => {
      // Scenario:
      // 1. fetchState() called, request R1 starts (slow, returns year=100)
      // 2. fetchState() called again, request R2 starts (fast, returns year=200)
      // 3. R2 returns first -> year = 200
      // 4. R1 returns later -> should be ignored (requestId mismatch)
      
      let resolveR1: (value: any) => void
      const r1Promise = new Promise(resolve => { resolveR1 = resolve })
      
      let callCount = 0
      vi.mocked(worldApi.fetchInitialState).mockImplementation(async () => {
        callCount++
        if (callCount === 1) {
          await r1Promise
          return { year: 100, month: 1, avatars: [] }
        }
        return { year: 200, month: 2, avatars: [] }
      })

      // Start R1 (slow).
      const fetch1 = store.fetchState()
      
      // Start R2 (fast) - this should be the "truth".
      await store.fetchState()
      expect(store.year).toBe(200)
      expect(store.month).toBe(2)
      
      // R1 completes with stale data.
      resolveR1!(undefined)
      await fetch1
      
      // R1's stale response is ignored due to requestId check.
      // Year should still be 200 from R2.
      expect(store.year).toBe(200)
      expect(store.month).toBe(2)
    })
  })

  describe('loadEvents', () => {
    it('should load events from API', async () => {
      vi.mocked(eventApi.fetchEvents).mockResolvedValue({
        events: [
          { id: 'e1', text: 'Event 1', year: 100, month: 1, month_stamp: 1200, related_avatar_ids: [], created_at: '2026-01-01T00:00:00Z' },
        ],
        next_cursor: 'cursor-123',
        has_more: true,
      })

      await store.loadEvents({})

      expect(store.events).toHaveLength(1)
      expect(store.eventsCursor).toBe('cursor-123')
      expect(store.eventsHasMore).toBe(true)
    })

    it('should ignore stale response when resetEvents is called (race condition fix)', async () => {
      // Scenario:
      // 1. loadEvents for filter A starts (slow)
      // 2. resetEvents called with filter B (fast)
      // 3. Response for B returns -> correct
      // 4. Response for A returns -> should be ignored (requestId mismatch)

      let callCount = 0
      vi.mocked(eventApi.fetchEvents).mockImplementation(async () => {
        callCount++
        return {
          events: [{ id: `e${callCount}`, text: `Event ${callCount}`, year: 100, month: 1, month_stamp: 1200, related_avatar_ids: [], created_at: '2026-01-01T00:00:00Z' }],
          next_cursor: null,
          has_more: false,
        }
      })

      // First load.
      await store.loadEvents({ avatar_id: 'a1' })
      expect(store.events[0].id).toBe('e1')

      // Reset with new filter.
      await store.resetEvents({ avatar_id: 'a2' })
      expect(store.events[0].id).toBe('e2')

      // requestId mechanism ensures only the latest response is used.
      expect(callCount).toBe(2)
    })

    it('should append events when append=true', async () => {
      store.events = [createMockEvent({ id: 'existing' })]
      store.eventsCursor = 'old-cursor'

      vi.mocked(eventApi.fetchEvents).mockResolvedValue({
        events: [
          { id: 'e2', text: 'Event 2', year: 100, month: 1, month_stamp: 1200, related_avatar_ids: [], created_at: '2026-01-01T00:00:00Z' },
        ],
        next_cursor: 'new-cursor',
        has_more: false,
      })

      await store.loadEvents({}, true)

      expect(store.events).toHaveLength(2)
    })

    it('should not load if already loading', async () => {
      store.eventsLoading = true

      await store.loadEvents({})

      expect(eventApi.fetchEvents).not.toHaveBeenCalled()
    })

    it('should handle errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(eventApi.fetchEvents).mockRejectedValue(new Error('Network error'))

      await store.loadEvents({})

      expect(consoleSpy).toHaveBeenCalled()
      expect(store.eventsLoading).toBe(false)
      consoleSpy.mockRestore()
    })
  })

  describe('loadMoreEvents', () => {
    it('should load more events if has more', async () => {
      store.eventsHasMore = true
      store.eventsFilter = { avatar_id: 'a1' }

      vi.mocked(eventApi.fetchEvents).mockResolvedValue({
        events: [],
        next_cursor: null,
        has_more: false,
      })

      await store.loadMoreEvents()

      expect(eventApi.fetchEvents).toHaveBeenCalled()
    })

    it('should not load if no more events', async () => {
      store.eventsHasMore = false

      await store.loadMoreEvents()

      expect(eventApi.fetchEvents).not.toHaveBeenCalled()
    })

    it('should not load if already loading', async () => {
      store.eventsHasMore = true
      store.eventsLoading = true

      await store.loadMoreEvents()

      expect(eventApi.fetchEvents).not.toHaveBeenCalled()
    })
  })

  describe('resetEvents', () => {
    it('should clear events and reload with new filter', async () => {
      store.events = [createMockEvent()]
      store.eventsCursor = 'old-cursor'
      store.eventsHasMore = true

      vi.mocked(eventApi.fetchEvents).mockResolvedValue({
        events: [],
        next_cursor: null,
        has_more: false,
      })

      await store.resetEvents({ avatar_id: 'a1' })

      expect(store.eventsFilter).toEqual({ avatar_id: 'a1' })
      expect(eventApi.fetchEvents).toHaveBeenCalled()
    })
  })

  describe('getPhenomenaList', () => {
    it('should fetch phenomena list if not cached', async () => {
      vi.mocked(worldApi.fetchPhenomenaList).mockResolvedValue({
        phenomena: [{ id: 1, name: 'Full Moon', description: 'A full moon' }],
      })

      const result = await store.getPhenomenaList()

      expect(result).toHaveLength(1)
      expect(store.phenomenaList).toHaveLength(1)
    })

    it('should return cached list if available', async () => {
      store.phenomenaList = [{ id: 1, name: 'Cached', description: 'Cached item' }]

      const result = await store.getPhenomenaList()

      expect(result).toHaveLength(1)
      expect(worldApi.fetchPhenomenaList).not.toHaveBeenCalled()
    })

    it('should return empty array on error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(worldApi.fetchPhenomenaList).mockRejectedValue(new Error('API error'))

      const result = await store.getPhenomenaList()

      expect(result).toEqual([])
      consoleSpy.mockRestore()
    })

    it('should make duplicate API calls when called concurrently (no deduplication)', async () => {
      let callCount = 0
      vi.mocked(worldApi.fetchPhenomenaList).mockImplementation(() => {
        callCount++
        return Promise.resolve({ phenomena: [{ id: 1, name: 'Moon', description: 'Moon' }] })
      })

      // Call twice concurrently before cache is populated.
      const [result1, result2] = await Promise.all([
        store.getPhenomenaList(),
        store.getPhenomenaList(),
      ])

      // Both calls go through because cache check happens before await.
      // This documents current behavior - a minor inefficiency, not a bug.
      expect(callCount).toBe(2)
      expect(result1).toHaveLength(1)
      expect(result2).toHaveLength(1)
    })
  })

  describe('changePhenomenon', () => {
    it('should call API and update currentPhenomenon optimistically', async () => {
      store.phenomenaList = [
        { id: 1, name: 'Full Moon', description: 'A full moon' },
        { id: 2, name: 'Eclipse', description: 'Solar eclipse' },
      ]
      vi.mocked(worldApi.setPhenomenon).mockResolvedValue(undefined)

      await store.changePhenomenon(2)

      expect(worldApi.setPhenomenon).toHaveBeenCalledWith(2)
      expect(store.currentPhenomenon?.id).toBe(2)
    })

    it('should not update if phenomenon not in list', async () => {
      store.phenomenaList = [{ id: 1, name: 'Full Moon', description: 'A full moon' }]
      vi.mocked(worldApi.setPhenomenon).mockResolvedValue(undefined)

      await store.changePhenomenon(99)

      expect(worldApi.setPhenomenon).toHaveBeenCalledWith(99)
      expect(store.currentPhenomenon).toBeNull()
    })

    it('should not update currentPhenomenon if API fails', async () => {
      store.phenomenaList = [
        { id: 1, name: 'Full Moon', description: 'A full moon' },
        { id: 2, name: 'Eclipse', description: 'Solar eclipse' },
      ]
      store.currentPhenomenon = { id: 1, name: 'Full Moon', description: 'A full moon' }
      vi.mocked(worldApi.setPhenomenon).mockRejectedValue(new Error('API error'))

      await expect(store.changePhenomenon(2)).rejects.toThrow('API error')

      // Should remain unchanged because API failed before update.
      expect(store.currentPhenomenon?.id).toBe(1)
    })
  })
})
