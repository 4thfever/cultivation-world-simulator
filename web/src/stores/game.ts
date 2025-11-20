import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Avatar {
    id: string
    name?: string
    x: number
    y: number
    action?: string
}

export type HoverTarget = {
    type: 'avatar' | 'region'
    id: string
    name?: string
}

export interface HoverSegment {
    text: string
    color?: string
}

export type HoverLine = HoverSegment[]

function normalizeHoverLines(raw: unknown): HoverLine[] {
    if (!Array.isArray(raw)) return []
    return raw.map((line) => {
        if (!Array.isArray(line)) {
            return [{ text: line != null ? String(line) : '' }]
        }
        const segments = line.map((segment) => {
            if (segment && typeof segment === 'object') {
                const record = segment as Record<string, unknown>
                const textValue = 'text' in record ? record.text : ''
                const colorValue = 'color' in record ? record.color : undefined
                const text = textValue != null ? String(textValue) : ''
                const color = typeof colorValue === 'string' && colorValue ? colorValue : undefined
                return { text, color }
            }
            return { text: segment != null ? String(segment) : '' }
        })
        return segments.length ? segments : [{ text: '' }]
    })
}

export interface GameEvent {
    id: string
    text: string
    content?: string
    year?: number
    month?: number
    monthStamp?: number
    relatedAvatarIds: string[]
    isMajor?: boolean
    isStory?: boolean
}

let localEventIdCounter = 0
function nextLocalEventId(prefix: string) {
    localEventIdCounter += 1
    return `${prefix}-${Date.now()}-${localEventIdCounter}`
}

function normalizeGameEvent(raw: unknown): GameEvent | null {
    if (raw == null) {
        return null
    }

    if (typeof raw === 'string') {
        return {
            id: nextLocalEventId('legacy'),
            text: raw,
            relatedAvatarIds: []
        }
    }

    if (typeof raw === 'object') {
        const record = raw as Record<string, unknown>
        const textSource = record.text ?? record.content ?? ''
        const text = typeof textSource === 'string' ? textSource : String(textSource ?? '')
        const idSource = record.id
        const id = typeof idSource === 'string' && idSource ? idSource : nextLocalEventId('evt')
        const relatedSource = record.related_avatar_ids ?? record.relatedAvatarIds ?? []
        const relatedAvatarIds = Array.isArray(relatedSource) ? relatedSource.map(val => String(val)) : []
        const content = typeof record.content === 'string' ? record.content : undefined
        const year = typeof record.year === 'number' ? record.year : undefined
        const month = typeof record.month === 'number' ? record.month : undefined
        const monthStampRaw = record.month_stamp ?? record.monthStamp
        const monthStamp = typeof monthStampRaw === 'number' ? monthStampRaw : undefined
        const isMajor = Boolean(record.is_major ?? record.isMajor ?? false)
        const isStory = Boolean(record.is_story ?? record.isStory ?? false)

        return {
            id,
            text: text || content || '',
            content,
            year,
            month,
            monthStamp,
            relatedAvatarIds,
            isMajor,
            isStory
        }
    }

    return {
        id: nextLocalEventId('legacy'),
        text: String(raw),
        relatedAvatarIds: []
    }
}

export const useGameStore = defineStore('game', () => {
    const isConnected = ref(false)
    const year = ref(0)
    const month = ref(0)
    const avatars = ref<Record<string, Avatar>>({})
    const events = ref<GameEvent[]>([]) // 添加事件列表状态
    const selectedTarget = ref<HoverTarget | null>(null)
    const hoverInfo = ref<HoverLine[]>([])
    const infoLoading = ref(false)
    const infoError = ref<string | null>(null)
    const hoverCache = new Map<string, HoverLine[]>()
    
    // 计算属性：转换为数组以便遍历
    const avatarList = computed(() => Object.values(avatars.value))

    function cacheKey(target: HoverTarget) {
        return `${target.type}:${target.id}`
    }

    function appendEvents(rawEvents: unknown) {
        if (!Array.isArray(rawEvents)) return
        const normalized = rawEvents
            .map((item) => normalizeGameEvent(item))
            .filter((evt): evt is GameEvent => !!evt)
        if (normalized.length) {
            events.value = [...normalized, ...events.value].slice(0, 100)
        }
    }

    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        // 开发环境下 Vite 代理会处理 /ws，生产环境直接连
        const host = window.location.host
        const ws = new WebSocket(`${protocol}//${host}/ws`)

        ws.onopen = () => {
            console.log('WS Connected')
            isConnected.value = true
        }

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                if (data.type === 'tick') {
                    year.value = data.year
                    month.value = data.month
                    
                    // 更新事件日志
                    appendEvents(data.events)
                    
                    // 更新 Avatars（增量更新逻辑：这里后端暂发的是全量/部分列表，直接覆盖位置）
                    if (data.avatars && Array.isArray(data.avatars)) {
                        data.avatars.forEach((av: Avatar) => {
                            if (avatars.value[av.id]) {
                                // 存在则更新
                                Object.assign(avatars.value[av.id], av)
                            } else {
                                // 不存在则创建（新角色）
                                avatars.value[av.id] = av
                            }
                        })
                    }
                }
            } catch (e) {
                console.error('WS Parse Error', e)
            }
        }

        ws.onclose = () => {
            console.log('WS Closed')
            isConnected.value = false
            // 简单的断线重连
            setTimeout(connect, 3000)
        }
    }

    // 初始加载（通过 HTTP 获取一次全量状态，因为 WS 只发增量或视口内）
    async function fetchInitialState() {
        try {
            const res = await fetch('/api/state')
            const data = await res.json()
            if (data.status === 'ok') {
                year.value = data.year
                month.value = data.month
                if (data.avatars) {
                    data.avatars.forEach((av: Avatar) => {
                        avatars.value[av.id] = av
                    })
                }
                appendEvents(data.events)
            }
        } catch (e) {
            console.error('Fetch State Error', e)
        }
    }

    async function fetchHoverInfo(target: HoverTarget) {
        const key = cacheKey(target)
        const cached = hoverCache.get(key)
        if (cached) {
            if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
                hoverInfo.value = cached
            }
            infoLoading.value = false
            infoError.value = null
            return
        }

        infoLoading.value = true
        infoError.value = null
        hoverInfo.value = []

        try {
            const query = new URLSearchParams({ type: target.type, id: target.id })
            const res = await fetch(`/api/hover?${query.toString()}`)
            if (!res.ok) {
                throw new Error(`加载失败：${res.status}`)
            }
            const data = await res.json()
            const lines = normalizeHoverLines(data.lines)
            hoverCache.set(key, lines)
            if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
                hoverInfo.value = lines
            }
        } catch (e) {
            if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
                infoError.value = e instanceof Error ? e.message : String(e)
                hoverInfo.value = []
            }
        } finally {
            if (selectedTarget.value && cacheKey(selectedTarget.value) === key) {
                infoLoading.value = false
            }
        }
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
        events, // 导出 events
        selectedTarget,
        hoverInfo,
        infoLoading,
        infoError,
        connect,
        fetchInitialState,
        openInfoPanel,
        closeInfoPanel
    }
})

