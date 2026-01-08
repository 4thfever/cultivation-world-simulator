<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, computed } from 'vue'
import { NConfigProvider, darkTheme, NMessageProvider } from 'naive-ui'
import { useWorldStore } from './stores/world'
import { useUiStore } from './stores/ui'
import { useSocketStore } from './stores/socket'
import { gameApi, type InitStatusDTO } from './api/game'

import GameCanvas from './components/game/GameCanvas.vue'
import InfoPanelContainer from './components/game/panels/info/InfoPanelContainer.vue'
import StatusBar from './components/layout/StatusBar.vue'
import EventPanel from './components/panels/EventPanel.vue'
import SystemMenu from './components/SystemMenu.vue'
import LoadingOverlay from './components/LoadingOverlay.vue'

// Stores
const worldStore = useWorldStore()
const uiStore = useUiStore()
const socketStore = useSocketStore()

// 初始化状态 - 持续轮询
const initStatus = ref<InitStatusDTO | null>(null)
const gameInitialized = ref(false)
const mapPreloaded = ref(false)
let pollInterval: ReturnType<typeof setInterval> | null = null

// 根据 spec: showLoading = initStatus !== 'ready'
// 注意：
// 1. initStatus 为 null 时显示加载界面（还没获取到状态）
// 2. initStatus 不是 ready 时显示加载界面
// 3. 前端还没初始化完成时也要显示加载界面
const showLoading = computed(() => {
  if (initStatus.value === null) return true
  if (initStatus.value.status !== 'ready') return true
  if (!gameInitialized.value) return true
  return false
})

const showMenu = ref(false)
const isManualPaused = ref(true)
const menuDefaultTab = ref<'save' | 'load' | 'create' | 'delete' | 'llm'>('load')

// 可以提前加载地图的阶段（宗门初始化后地图数据就 ready 了）。
const MAP_READY_PHASES = ['initializing_sects', 'generating_avatars', 'checking_llm', 'generating_initial_events']
// 可以提前加载角色的阶段（world 创建后）。
const AVATAR_READY_PHASES = ['checking_llm', 'generating_initial_events']

const avatarsPreloaded = ref(false)

// 轮询初始化状态
async function pollInitStatus() {
  try {
    const res = await gameApi.fetchInitStatus()
    const prevStatus = initStatus.value?.status
    initStatus.value = res
    
    // 提前加载地图：当进入特定阶段且还没预加载过时。
    if (!mapPreloaded.value && MAP_READY_PHASES.includes(res.phase_name)) {
      mapPreloaded.value = true
      worldStore.preloadMap()
    }
    
    // 提前加载角色：当进入 checking_llm 或之后阶段。
    if (!avatarsPreloaded.value && AVATAR_READY_PHASES.includes(res.phase_name)) {
      avatarsPreloaded.value = true
      worldStore.preloadAvatars()
    }
    
    // 从非 ready 变为 ready 时，初始化前端
    // 注意：prevStatus 为 undefined 时也算"非 ready"
    if (prevStatus !== 'ready' && res.status === 'ready') {
      await initializeGame()
      // ready 后停止轮询
      stopPolling()
    }
  } catch (e) {
    console.error('Failed to fetch init status:', e)
  }
}

async function initializeGame() {
  if (gameInitialized.value) {
    // 重新加载存档时，重新初始化
    worldStore.reset()
    uiStore.clearSelection()
  }
  
  // 初始化 Socket 连接（如果未连接）
  if (!socketStore.isConnected) {
    socketStore.init()
  }
  // 初始化世界状态（获取地图、角色等数据）
  await worldStore.initialize()
  
  gameInitialized.value = true
  // 自动取消暂停，让游戏开始运行
  isManualPaused.value = false
  console.log('[App] Game initialized.')
}

function startPolling() {
  // 立即获取一次
  pollInitStatus()
  // 每秒轮询
  pollInterval = setInterval(pollInitStatus, 1000)
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  startPolling()
})

// 导出方法供 socket store 调用
function openLLMConfig() {
  menuDefaultTab.value = 'llm'
  showMenu.value = true
}

// 暴露给全局以便 socket store 可以调用
;(window as any).__openLLMConfig = openLLMConfig

onUnmounted(() => {
  socketStore.disconnect()
  window.removeEventListener('keydown', handleKeydown)
  stopPolling()
})

function handleKeydown(e: KeyboardEvent) {
  // 只在游戏界面响应键盘事件
  if (showLoading.value) return
  
  if (e.key === 'Escape') {
    if (uiStore.selectedTarget) {
      uiStore.clearSelection()
    } else {
      showMenu.value = !showMenu.value
    }
  }
}

function handleSelection(target: { type: 'avatar' | 'region'; id: string; name?: string }) {
  uiStore.select(target.type, target.id)
}

function handleMenuClose() {
  showMenu.value = false
}

function toggleManualPause() {
  isManualPaused.value = !isManualPaused.value
}

// 监听菜单状态和手动暂停状态，控制游戏暂停/继续
watch([showMenu, isManualPaused], ([menuVisible, manualPaused]) => {
  // 只在游戏已准备好时控制暂停
  if (!gameInitialized.value) return
  
  if (menuVisible || manualPaused) {
    gameApi.pauseGame().catch(console.error)
  } else {
    gameApi.resumeGame().catch(console.error)
  }
})
</script>

<template>
  <n-config-provider :theme="darkTheme">
    <n-message-provider>
      <!-- Loading Overlay - 盖在游戏上面 -->
      <LoadingOverlay 
        v-if="showLoading"
        :status="initStatus"
      />

      <!-- Game UI - 始终渲染 -->
      <div class="app-layout">
        <StatusBar />
        
        <div class="main-content">
          <div class="map-container">
            <!-- 顶部控制栏 -->
            <div class="top-controls">
              <!-- 暂停/播放按钮 -->
              <button class="control-btn pause-toggle" @click="toggleManualPause" :title="isManualPaused ? '继续游戏' : '暂停游戏'">
                <!-- 播放图标 (当暂停时显示) -->
                <svg v-if="isManualPaused" viewBox="0 0 24 24" width="24" height="24">
                  <path fill="currentColor" d="M8 5v14l11-7z"/>
                </svg>
                <!-- 暂停图标 (当播放时显示) -->
                <svg v-else viewBox="0 0 24 24" width="24" height="24">
                  <path fill="currentColor" d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                </svg>
              </button>

              <!-- 菜单按钮 -->
              <button class="control-btn menu-toggle" @click="showMenu = true">
                <svg viewBox="0 0 24 24" width="24" height="24">
                  <path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
                </svg>
              </button>
            </div>

            <!-- 暂停状态提示 -->
            <div v-if="isManualPaused" class="pause-indicator">
              <div class="pause-text">已暂停</div>
            </div>

            <GameCanvas
              @avatarSelected="handleSelection"
              @regionSelected="handleSelection"
            />
            <InfoPanelContainer />
          </div>
          <aside class="sidebar">
            <EventPanel />
          </aside>
        </div>

        <SystemMenu 
          :visible="showMenu"
          :default-tab="menuDefaultTab"
          @close="handleMenuClose"
        />
      </div>
    </n-message-provider>
  </n-config-provider>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  background: #000;
  color: #eee;
  overflow: hidden;
  position: relative;
}

.main-content {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.map-container {
  flex: 1;
  position: relative;
  background: #111;
  overflow: hidden;
}

.top-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 100;
  display: flex;
  gap: 10px;
}

.control-btn {
  background: rgba(0,0,0,0.5);
  border: 1px solid #444;
  color: #ddd;
  width: 40px;
  height: 40px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.control-btn:hover {
  background: rgba(0,0,0,0.8);
  border-color: #666;
  color: #fff;
}

.pause-indicator {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 90;
  pointer-events: none;
}

.pause-text {
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  letter-spacing: 2px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(4px);
}

.sidebar {
  width: 400px;
  background: #181818;
  border-left: 1px solid #333;
  display: flex;
  flex-direction: column;
  z-index: 20;
}
</style>
