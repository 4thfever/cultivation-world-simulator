import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type {
  Avatar,
  GameEvent,
  HoverLine,
  HoverTarget,
  TickPayload,
  IAvatarDetail,
  DetailInfo
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
  const detailInfo = ref<DetailInfo | null>(null)
  const infoLoading = ref(false)
  const infoError = ref<string | null>(null)
  const hoverCache = new Map<string, HoverLine[]>()
  
  // 新增：用于标记世界是否被重置（读档）
  const worldVersion = ref(0)

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

    // Tick means time passed, so cache is stale
    hoverCache.clear()
    
    // If panel is open, silently refresh content to show latest status
    if (selectedTarget.value) {
      if (selectedTarget.value.type === 'avatar') {
        fetchDetailInfo(selectedTarget.value, { silent: true })
      } else {
        fetchHoverInfo(selectedTarget.value, { force: true, silent: true })
      }
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
      
      // 重置事件列表，而不是追加，因为是全新状态
      events.value = []
      appendEvents(data.events)
    } catch (error) {
      console.error('Fetch State Error', error)
    }
  }

  async function fetchDetailInfo(target: HoverTarget, options: { silent?: boolean } = {}) {
    const { silent = false } = options
    if (!silent) {
      infoLoading.value = true
      infoError.value = null
      detailInfo.value = null
    }

    try {
      const data = await gameApi.getDetailInfo(target)
      // Check if result matches current selection (race condition)
      if (selectedTarget.value && selectedTarget.value.id === target.id) {
        detailInfo.value = data
        // If fallback is true, we might also want to populate hoverInfo for legacy support,
        // but InfoPanel should handle detailInfo with lines fallback.
      }
    } catch (error) {
      if (selectedTarget.value && selectedTarget.value.id === target.id) {
        if (!silent) {
          infoError.value = error instanceof Error ? error.message : String(error)
          detailInfo.value = null
        }
      }
    } finally {
      if (selectedTarget.value && selectedTarget.value.id === target.id) {
        if (!silent) {
          infoLoading.value = false
        }
      }
    }
  }

  async function fetchHoverInfo(target: HoverTarget, options: { force?: boolean, silent?: boolean } = {}) {
    const { force = false, silent = false } = options
    const key = cacheKey(target)
    
    if (!force) {
      const cached = hoverCache.get(key)
      if (cached) {
        if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
          hoverInfo.value = cached
        }
        if (!silent) {
          infoLoading.value = false
          infoError.value = null
        }
        return
      }
    }

    if (!silent) {
      infoLoading.value = true
      infoError.value = null
      if (!force) hoverInfo.value = []
    }

    try {
      const data = await gameApi.getHoverInfo(target)
      const lines = normalizeHoverLines(data.lines)
      hoverCache.set(key, lines)
      if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
        hoverInfo.value = lines
      }
    } catch (error) {
      if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
        if (!silent) {
          infoError.value = error instanceof Error ? error.message : String(error)
          hoverInfo.value = []
        }
      }
    } finally {
      if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
        if (!silent) {
          infoLoading.value = false
        }
      }
    }
  }

  async function setLongTermObjective(avatarId: string, content: string) {
    await gameApi.setLongTermObjective(avatarId, content)
    // 成功后刷新 info panel
    if (selectedTarget.value && selectedTarget.value.id === avatarId && selectedTarget.value.type === 'avatar') {
      await fetchDetailInfo(selectedTarget.value, { silent: true })
    }
  }

  async function clearLongTermObjective(avatarId: string) {
    await gameApi.clearLongTermObjective(avatarId)
    // 成功后刷新 info panel
    if (selectedTarget.value && selectedTarget.value.id === avatarId && selectedTarget.value.type === 'avatar') {
      await fetchDetailInfo(selectedTarget.value, { silent: true })
    }
  }

  async function reloadGame(filename: string) {
    // 1. 调用加载接口
    await gameApi.loadGame(filename)
    
    // 2. 清空前端状态
    avatars.value = {}
    events.value = []
    hoverCache.clear()
    hoverInfo.value = []
    selectedTarget.value = null
    
    // 3. 重新获取初始状态
    await fetchInitialState()
    
    // 4. 更新世界版本，触发特定组件重绘
    worldVersion.value++
    
    return true
  }

  function connect() {
    gateway.connect()
  }

  function disconnect() {
    gateway.disconnect()
  }

  function openInfoPanel(target: HoverTarget) {
    selectedTarget.value = target
    if (target.type === 'avatar' || target.type === 'region') {
      fetchDetailInfo(target)
    } else {
      fetchHoverInfo(target)
    }
  }

  function closeInfoPanel() {
    selectedTarget.value = null
    infoError.value = null
    hoverInfo.value = []
    detailInfo.value = null
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
    detailInfo,
    infoLoading,
    infoError,
    worldVersion, // 导出
    connect,
    disconnect,
    fetchInitialState,
    openInfoPanel,
    closeInfoPanel,
    setLongTermObjective,
    clearLongTermObjective,
    reloadGame
  }
})
