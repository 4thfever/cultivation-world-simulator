import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useEventStore } from '@/stores/event'

vi.mock('@/api', () => ({
  eventApi: {
    fetchEvents: vi.fn(),
  },
}))

import { eventApi } from '@/api'

describe('useEventStore', () => {
  let store: ReturnType<typeof useEventStore>

  beforeEach(() => {
    store = useEventStore()
    store.reset()
    vi.clearAllMocks()
  })

  it('records merge duration when handling tick events', () => {
    store.addEvents([
      {
        id: 'e1',
        text: 'event',
        content: 'event',
        related_avatar_ids: [],
        is_major: false,
        is_story: false,
        created_at: 1,
      },
    ] as any, 1, 1)

    expect(store.events).toHaveLength(1)
    expect(store.lastMergeDurationMs).toBeGreaterThanOrEqual(0)
  })

  it('records load duration and keeps timeline in ascending order', async () => {
    vi.mocked(eventApi.fetchEvents).mockResolvedValue({
      events: [
        {
          id: 'e2',
          text: 'newer',
          content: 'newer',
          year: 1,
          month: 2,
          month_stamp: 14,
          related_avatar_ids: [],
          is_major: false,
          is_story: false,
          created_at: 2,
        },
        {
          id: 'e1',
          text: 'older',
          content: 'older',
          year: 1,
          month: 1,
          month_stamp: 13,
          related_avatar_ids: [],
          is_major: false,
          is_story: false,
          created_at: 1,
        },
      ],
      next_cursor: null,
      has_more: false,
    })

    await store.loadEvents({})

    expect(store.lastLoadDurationMs).toBeGreaterThanOrEqual(0)
    expect(store.events.map((e) => e.id)).toEqual(['e1', 'e2'])
  })

  it('loadEvents passes sect_id to fetchEvents', async () => {
    vi.mocked(eventApi.fetchEvents).mockResolvedValue({
      events: [],
      next_cursor: null,
      has_more: false,
    })

    await store.loadEvents({ sect_id: 5 })

    expect(eventApi.fetchEvents).toHaveBeenCalledWith(
      expect.objectContaining({ sect_id: 5, limit: 100 })
    )
  })

  it('addEvents filters by relatedSects when filter.sect_id is set', () => {
    store.eventsFilter = { sect_id: 1 }
    store.addEvents(
      [
        {
          id: 'e1',
          text: 'a',
          content: 'a',
          year: 1,
          month: 1,
          month_stamp: 13,
          related_avatar_ids: [],
          related_sects: [1, 2],
          is_major: false,
          is_story: false,
          created_at: 1,
        } as any,
        {
          id: 'e2',
          text: 'b',
          content: 'b',
          year: 1,
          month: 2,
          month_stamp: 14,
          related_avatar_ids: [],
          related_sects: [2],
          is_major: false,
          is_story: false,
          created_at: 2,
        } as any,
      ],
      1,
      2
    )

    expect(store.events).toHaveLength(1)
    expect(store.events[0].id).toBe('e1')
  })

  it('loadEvents passes major_scope to fetchEvents', async () => {
    vi.mocked(eventApi.fetchEvents).mockResolvedValue({
      events: [],
      next_cursor: null,
      has_more: false,
    })

    await store.loadEvents({ major_scope: 'major' })

    expect(eventApi.fetchEvents).toHaveBeenCalledWith(
      expect.objectContaining({ major_scope: 'major', limit: 100 })
    )
  })

  it('addEvents filters major events with story excluded when filter.major_scope is major', () => {
    store.eventsFilter = { major_scope: 'major' }
    store.addEvents(
      [
        {
          id: 'e1',
          text: 'major',
          content: 'major',
          year: 1,
          month: 1,
          month_stamp: 13,
          related_avatar_ids: [],
          is_major: true,
          is_story: false,
          created_at: 1,
        } as any,
        {
          id: 'e2',
          text: 'story',
          content: 'story',
          year: 1,
          month: 2,
          month_stamp: 14,
          related_avatar_ids: [],
          is_major: true,
          is_story: true,
          created_at: 2,
        } as any,
        {
          id: 'e3',
          text: 'minor',
          content: 'minor',
          year: 1,
          month: 3,
          month_stamp: 15,
          related_avatar_ids: [],
          is_major: false,
          is_story: false,
          created_at: 3,
        } as any,
      ],
      1,
      3
    )

    expect(store.events).toHaveLength(1)
    expect(store.events[0].id).toBe('e1')
  })

  it('addEvents includes story events when filter.major_scope is minor', () => {
    store.eventsFilter = { major_scope: 'minor' }
    store.addEvents(
      [
        {
          id: 'e1',
          text: 'major',
          content: 'major',
          year: 1,
          month: 1,
          month_stamp: 13,
          related_avatar_ids: [],
          is_major: true,
          is_story: false,
          created_at: 1,
        } as any,
        {
          id: 'e2',
          text: 'story',
          content: 'story',
          year: 1,
          month: 2,
          month_stamp: 14,
          related_avatar_ids: [],
          is_major: true,
          is_story: true,
          created_at: 2,
        } as any,
        {
          id: 'e3',
          text: 'minor',
          content: 'minor',
          year: 1,
          month: 3,
          month_stamp: 15,
          related_avatar_ids: [],
          is_major: false,
          is_story: false,
          created_at: 3,
        } as any,
      ],
      1,
      3
    )

    expect(store.events).toHaveLength(2)
    expect(store.events.map((e) => e.id)).toEqual(['e2', 'e3'])
  })
})

