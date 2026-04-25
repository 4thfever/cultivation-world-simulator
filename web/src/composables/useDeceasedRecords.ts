import { ref, shallowRef } from 'vue'

import { eventApi } from '@/api/modules/event'
import { worldApi } from '@/api/modules/world'
import { mapDeceasedList, type DeceasedRecordView } from '@/api/mappers/deceased'
import type { EventDTO } from '@/types/api'
import { logError } from '@/utils/appError'

interface UseDeceasedRecordsOptions {
  logScope: string
}

export function useDeceasedRecords(options: UseDeceasedRecordsOptions) {
  const recordsLoading = ref(false)
  const recordsLoaded = ref(false)
  const records = shallowRef<DeceasedRecordView[]>([])
  const selectedRecord = ref<DeceasedRecordView | null>(null)
  const eventsLoading = ref(false)
  const events = shallowRef<EventDTO[]>([])

  let recordsRequestId = 0
  let eventsRequestId = 0

  async function fetchRecords() {
    const currentRequestId = ++recordsRequestId
    recordsLoading.value = true
    try {
      const dtos = await worldApi.fetchDeceasedList()
      if (currentRequestId !== recordsRequestId) return

      records.value = mapDeceasedList(dtos)
      recordsLoaded.value = true
    } catch (error) {
      if (currentRequestId !== recordsRequestId) return

      logError(`${options.logScope} fetch deceased`, error)
      records.value = []
      recordsLoaded.value = false
    } finally {
      if (currentRequestId === recordsRequestId) {
        recordsLoading.value = false
      }
    }
  }

  async function fetchEvents(avatarId: string) {
    const currentRequestId = ++eventsRequestId
    eventsLoading.value = true
    try {
      const res = await eventApi.fetchEvents({ avatar_id: avatarId, limit: 50 })
      if (
        currentRequestId !== eventsRequestId ||
        selectedRecord.value?.id !== avatarId
      ) {
        return
      }

      events.value = res.events
    } catch (error) {
      if (currentRequestId !== eventsRequestId) return

      logError(`${options.logScope} fetch events`, error)
      events.value = []
    } finally {
      if (currentRequestId === eventsRequestId) {
        eventsLoading.value = false
      }
    }
  }

  function selectRecord(record: DeceasedRecordView) {
    selectedRecord.value = record
    events.value = []
    void fetchEvents(record.id)
  }

  function resetSelection() {
    eventsRequestId++
    selectedRecord.value = null
    events.value = []
    eventsLoading.value = false
  }

  function backToList() {
    resetSelection()
  }

  function resetAll() {
    recordsRequestId++
    recordsLoading.value = false
    recordsLoaded.value = false
    records.value = []
    resetSelection()
  }

  return {
    recordsLoading,
    recordsLoaded,
    records,
    selectedRecord,
    eventsLoading,
    events,
    fetchRecords,
    selectRecord,
    backToList,
    resetSelection,
    resetAll,
  }
}
