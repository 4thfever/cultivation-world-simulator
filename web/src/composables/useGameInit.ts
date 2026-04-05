import { ref, onMounted, onUnmounted } from 'vue'
import { useSystemStore } from '@/stores/system'
import { useWorldStore } from '@/stores/world'
import { useSocketStore } from '@/stores/socket'
import { GAME_PHASES } from '@/constants/game'
import { storeToRefs } from 'pinia'

import { useTextures } from '@/components/game/composables/useTextures'
import { logError, logWarn } from '@/utils/appError'

interface UseGameInitOptions {
  onIdle?: () => void
}

type InitPhaseName =
  | (typeof GAME_PHASES.MAP_READY)[number]
  | (typeof GAME_PHASES.AVATAR_READY)[number]
  | (typeof GAME_PHASES.TEXTURES_READY)[number]

function isPhaseIn(list: readonly string[], phaseName: string): phaseName is InitPhaseName {
  return list.includes(phaseName)
}

export function useGameInit(options: UseGameInitOptions = {}) {
  const systemStore = useSystemStore()
  const worldStore = useWorldStore()
  const socketStore = useSocketStore()
  const { loadBaseTextures } = useTextures()

  const { initStatus, isInitialized, isLoading } = storeToRefs(systemStore)
  
  // 内部变量
  const mapPreloaded = ref(false)
  const avatarsPreloaded = ref(false)
  const texturesPreloaded = ref(false)
  const initializeDurationMs = ref(0)
  const lastPollDurationMs = ref(0)
  
  let pollInterval: ReturnType<typeof setInterval> | null = null

  // Methods
  async function initializeGame() {
    const start = performance.now()
    if (isInitialized.value) {
      // 重新加载存档时，重新初始化
      worldStore.reset()
    }
    
    // 初始化 Socket 连接
    if (!socketStore.isConnected) {
      socketStore.init()
    }
    
    // 初始化世界状态
    await worldStore.initialize()
    
    // 重新加载纹理以确保新生成的角色头像被加载
    await loadBaseTextures()
    
    systemStore.setInitialized(true)
    initializeDurationMs.value = performance.now() - start
  }

  async function pollInitStatus() {
    const pollStart = performance.now()
    try {
      const prevStatus = initStatus.value?.status
      const res = await systemStore.fetchInitStatus()
      
      if (!res) return

      // Idle check
      if (res.status === 'idle') {
        if (prevStatus !== 'idle') {
          options.onIdle?.()
        }
        // 如果后端是 idle，确保前端状态也是重置的
        if (isInitialized.value) {
            systemStore.setInitialized(false)
            worldStore.reset()
        }
        // 重置预加载标记
        mapPreloaded.value = false
        avatarsPreloaded.value = false
        texturesPreloaded.value = false
      }

      // 提前加载地图
      if (!mapPreloaded.value && isPhaseIn(GAME_PHASES.MAP_READY, res.phase_name)) {
        mapPreloaded.value = true
        worldStore.preloadMap()
      }
      
      // 提前加载角色
      if (!avatarsPreloaded.value && isPhaseIn(GAME_PHASES.AVATAR_READY, res.phase_name)) {
        avatarsPreloaded.value = true
        worldStore.preloadAvatars()
      }
      
      // 提前加载纹理资源（利用后端生成事件等待期）
      if (!texturesPreloaded.value && isPhaseIn(GAME_PHASES.TEXTURES_READY, res.phase_name)) {
        texturesPreloaded.value = true
        loadBaseTextures().catch((e) => logWarn('GameInit preload textures', e))
      }
      
      // 状态跃迁：非 Ready -> Ready
      if (prevStatus !== 'ready' && res.status === 'ready' && !isInitialized.value) {
        await initializeGame()
        // 不要停止轮询，否则 reset 之后无法检测到状态变化
        // stopPolling()
      }
    } catch (e) {
      logError('GameInit fetch init status', e)
    } finally {
      lastPollDurationMs.value = performance.now() - pollStart
    }
  }

  function startPolling() {
    pollInitStatus()
    pollInterval = setInterval(pollInitStatus, 1000)
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }

  onMounted(() => {
    startPolling()
  })

  onUnmounted(() => {
    stopPolling()
    socketStore.disconnect()
  })

  return {
    initStatus,
    gameInitialized: isInitialized, // Alias for compatibility
    showLoading: isLoading,
    mapPreloaded,
    avatarsPreloaded,
    initializeDurationMs,
    lastPollDurationMs,
    initializeGame,
    startPolling,
    stopPolling
  }
}
