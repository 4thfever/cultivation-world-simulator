import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type {
  Avatar,
  GameEvent,
  HoverLine,
  HoverTarget,
  TickPayload
} from '../types/game'
import { gameApi } from '../services/gameApi'
import { createGameGateway } from '../services/gameGateway'
import { normalizeGameEvent, normalizeHoverLines } from '../utils/normalizers'

const MAX_EVENTS = 200

function cacheKey(target: HoverTarget) {
  return `${target.type}:${target.id}`
}

function eventRank(event: GameEvent) {
  if (typeof event.monthStamp === 'number') {
    return event.monthStamp
  }
  if (typeof event.year === 'number' && typeof event.month === 'number') {
    return event.year * 12 + event.month
  }
  return -Infinity
}

function sortEventsDescending(a: GameEvent, b: GameEvent) {
  const diff = eventRank(b) - eventRank(a)
  if (diff !== 0) return diff
  return b.id.localeCompare(a.id)
}

export const useGameStore = defineStore('game', () => {
  const isConnected = ref(false)
  const year = ref(0)
  const month = ref(0)
  const avatars = ref<Record<string, Avatar>>({})
  const events = ref<GameEvent[]>([])
  const selectedTarget = ref<HoverTarget | null>(null)
  const hoverInfo = ref<HoverLine[]>([])
  const infoLoading = ref(false)
  const infoError = ref<string | null>(null)
  const hoverCache = new Map<string, HoverLine[]>()

  const avatarList = computed(() => Object.values(avatars.value))

  const gateway = createGameGateway({
    onTick: handleTickPayload,
    onStatusChange: (connected) => {
      isConnected.value = connected
    },
    onError: (error) => {
      console.error('WS Error', error)
    }
  })

  function handleTickPayload(payload: TickPayload) {
    year.value = payload.year
    month.value = payload.month
    appendEvents(payload.events)

    if (Array.isArray(payload.avatars)) {
      mergeAvatars(payload.avatars)
    }
  }

  function mergeAvatars(list: Avatar[]) {
    list.forEach((av) => {
      const existing = avatars.value[av.id]
      avatars.value[av.id] = existing ? { ...existing, ...av } : { ...av }
    })
  }

  function appendEvents(rawEvents: unknown) {
    if (!Array.isArray(rawEvents) || !rawEvents.length) return
    const bucket = new Map(events.value.map((evt) => [evt.id, evt]))
    let changed = false

    rawEvents.forEach((item) => {
      const evt = normalizeGameEvent(item)
      if (!evt) return
      bucket.set(evt.id, evt)
      changed = true
    })

    if (!changed) return

    const nextEvents = [...bucket.values()].sort(sortEventsDescending).slice(0, MAX_EVENTS)
    events.value = nextEvents
  }

  async function fetchInitialState() {
    try {
      const data = await gameApi.getInitialState()
      if (data.status !== 'ok') return
      year.value = data.year
      month.value = data.month
      if (Array.isArray(data.avatars)) {
        const nextAvatars: Record<string, Avatar> = {}
        data.avatars.forEach((av) => {
          nextAvatars[av.id] = av
        })
        avatars.value = nextAvatars
      }
      appendEvents(data.events)
    } catch (error) {
      console.error('Fetch State Error', error)
    }
  }

  async function fetchHoverInfo(target: HoverTarget, forceRefresh = false) {
    const key = cacheKey(target)
    if (!forceRefresh) {
      const cached = hoverCache.get(key)
      if (cached) {
        if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
          hoverInfo.value = cached
        }
        infoLoading.value = false
        infoError.value = null
        return
      }
    }

    infoLoading.value = true
    infoError.value = null
    if (!forceRefresh) hoverInfo.value = []

    try {
      const data = await gameApi.getHoverInfo(target)
      const lines = normalizeHoverLines(data.lines)
      hoverCache.set(key, lines)
      if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
        hoverInfo.value = lines
      }
    } catch (error) {
      if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
        infoError.value = error instanceof Error ? error.message : String(error)
        hoverInfo.value = []
      }
    } finally {
      if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
        infoLoading.value = false
      }
    }
  }

  async function setLongTermObjective(avatarId: string, content: string) {
    await gameApi.setLongTermObjective(avatarId, content)
    // 成功后刷新 info panel
    if (selectedTarget.value && selectedTarget.value.id === avatarId && selectedTarget.value.type === 'avatar') {
      await fetchHoverInfo(selectedTarget.value, true)
    }
  }

  async function clearLongTermObjective(avatarId: string) {
    await gameApi.clearLongTermObjective(avatarId)
    // 成功后刷新 info panel
    if (selectedTarget.value && selectedTarget.value.id === avatarId && selectedTarget.value.type === 'avatar') {
      await fetchHoverInfo(selectedTarget.value, true)
    }
  }

  function connect() {
    gateway.connect()
  }

  function disconnect() {
    gateway.disconnect()
  }

  function openInfoPanel(target: HoverTarget) {
    selectedTarget.value = target
    fetchHoverInfo(target)
  }

  function closeInfoPanel() {
    selectedTarget.value = null
    infoError.value = null
    hoverInfo.value = []
    infoLoading.value = false
  }

  return {
    isConnected,
    year,
    month,
    avatars,
    avatarList,
    events,
    selectedTarget,
    hoverInfo,
    infoLoading,
    infoError,
    connect,
    disconnect,
    fetchInitialState,
    openInfoPanel,
    closeInfoPanel,
    setLongTermObjective,
    clearLongTermObjective
  }
})
