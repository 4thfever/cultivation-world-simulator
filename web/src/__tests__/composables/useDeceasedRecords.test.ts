import { describe, expect, it, vi, beforeEach } from 'vitest'

const mocks = vi.hoisted(() => ({
  fetchDeceasedList: vi.fn(),
  fetchEvents: vi.fn(),
}))

vi.mock('@/api/modules/world', () => ({
  worldApi: {
    fetchDeceasedList: mocks.fetchDeceasedList,
  },
}))

vi.mock('@/api/modules/event', () => ({
  eventApi: {
    fetchEvents: mocks.fetchEvents,
  },
}))

import { useDeceasedRecords } from '@/composables/useDeceasedRecords'
import type { DeceasedRecordView } from '@/api/mappers/deceased'

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

const recordA: DeceasedRecordView = {
  id: 'dead-a',
  name: 'A',
  gender: 'male',
  ageAtDeath: 100,
  realmDisplay: 'Realm',
  stageDisplay: 'Stage',
  deathReason: 'Reason',
  deathYear: 1,
  deathMonth: 1,
  sectName: '',
  alignment: '',
  backstory: null,
  customPicId: null,
}

const recordB: DeceasedRecordView = {
  ...recordA,
  id: 'dead-b',
  name: 'B',
}

describe('useDeceasedRecords', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('keeps only the latest selected record events', async () => {
    const first = deferred<{ events: any[] }>()
    const second = deferred<{ events: any[] }>()
    mocks.fetchEvents
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise)

    const state = useDeceasedRecords({ logScope: 'test' })

    state.selectRecord(recordA)
    state.selectRecord(recordB)

    second.resolve({ events: [{ id: 'event-b', content: 'B' }] })
    await second.promise
    await Promise.resolve()

    expect(state.events.value).toEqual([{ id: 'event-b', content: 'B' }])

    first.resolve({ events: [{ id: 'event-a', content: 'A' }] })
    await first.promise
    await Promise.resolve()

    expect(state.events.value).toEqual([{ id: 'event-b', content: 'B' }])
  })

  it('ignores pending event responses after resetting selection', async () => {
    const pending = deferred<{ events: any[] }>()
    mocks.fetchEvents.mockReturnValueOnce(pending.promise)

    const state = useDeceasedRecords({ logScope: 'test' })

    state.selectRecord(recordA)
    state.resetSelection()

    pending.resolve({ events: [{ id: 'late-event', content: 'late' }] })
    await pending.promise
    await Promise.resolve()

    expect(state.selectedRecord.value).toBeNull()
    expect(state.events.value).toEqual([])
    expect(state.eventsLoading.value).toBe(false)
  })
})
