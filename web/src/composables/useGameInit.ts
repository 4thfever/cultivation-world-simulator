import { ref, onMounted, onUnmounted } from 'vue'
import { useSystemStore } from '@/stores/system'
import { useWorldStore } from '@/stores/world'
import { useSocketStore } from '@/stores/socket'
import { GAME_PHASES } from '@/constants/game'
import { storeToRefs } from 'pinia'

import { useTextures } from '@/components/game/composables/useTextures'

interface UseGameInitOptions {
  onIdle?: () => void
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
  
  let pollInterval: ReturnType<typeof setInterval> | null = null

  // Methods
  async function initializeGame() {
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
    console.log('[GameInit] Reloading textures for new avatars...')
    await loadBaseTextures()
    
    systemStore.setInitialized(true)
    console.log('[GameInit] Game initialized.')
  }

  async function pollInitStatus() {
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
      if (!mapPreloaded.value && GAME_PHASES.MAP_READY.includes(res.phase_name as any)) {
        mapPreloaded.value = true
        worldStore.preloadMap()
      }
      
      // 提前加载角色
      if (!avatarsPreloaded.value && GAME_PHASES.AVATAR_READY.includes(res.phase_name as any)) {
        avatarsPreloaded.value = true
        worldStore.preloadAvatars()
      }
      
      // 提前加载纹理资源（利用后端生成事件等待期）
      if (!texturesPreloaded.value && GAME_PHASES.TEXTURES_READY.includes(res.phase_name as any)) {
        texturesPreloaded.value = true
        loadBaseTextures().catch(e => console.warn('[GameInit] Failed to preload textures', e))
      }
      
      // 状态跃迁：非 Ready -> Ready
      if (prevStatus !== 'ready' && res.status === 'ready') {
        await initializeGame()
        // 不要停止轮询，否则 reset 之后无法检测到状态变化
        // stopPolling()
      }
    } catch (e) {
      console.error('Failed to fetch init status:', e)
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
    initializeGame,
    startPolling,
    stopPolling
  }
}
