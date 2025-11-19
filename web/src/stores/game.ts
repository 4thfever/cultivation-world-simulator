import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Avatar {
    id: string
    name?: string
    x: number
    y: number
    action?: string
}

export const useGameStore = defineStore('game', () => {
    const isConnected = ref(false)
    const year = ref(0)
    const month = ref(0)
    const avatars = ref<Record<string, Avatar>>({})
    
    // 计算属性：转换为数组以便遍历
    const avatarList = computed(() => Object.values(avatars.value))

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
            }
        } catch (e) {
            console.error('Fetch State Error', e)
        }
    }

    return {
        isConnected,
        year,
        month,
        avatars,
        avatarList,
        connect,
        fetchInitialState
    }
})

