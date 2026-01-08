<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { NConfigProvider, darkTheme, NMessageProvider } from 'naive-ui'
import { useWorldStore } from './stores/world'
import { useUiStore } from './stores/ui'
import { useSocketStore } from './stores/socket'
import { gameApi } from './api/game'

import GameCanvas from './components/game/GameCanvas.vue'
import InfoPanelContainer from './components/game/panels/info/InfoPanelContainer.vue'
import StatusBar from './components/layout/StatusBar.vue'
import EventPanel from './components/panels/EventPanel.vue'
import SystemMenu from './components/SystemMenu.vue'

// Stores
const worldStore = useWorldStore()
const uiStore = useUiStore()
const socketStore = useSocketStore()

const showMenu = ref(false)
// 启动时默认暂停，让用户选择"新游戏"或"加载存档"后再继续。
const isManualPaused = ref(true)
const menuDefaultTab = ref<'save' | 'load' | 'create' | 'delete' | 'llm'>('load')

onMounted(async () => {
  // 初始化 Socket 连接
  socketStore.init()
  // 初始化世界状态
  await worldStore.initialize()
  window.addEventListener('keydown', handleKeydown)
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
})

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (uiStore.selectedTarget) {
      uiStore.clearSelection()
    } else {
      showMenu.value = !showMenu.value
    }
  } else if (e.key === ' ') {
    // Space to toggle pause? Optional but good UX
    // toggleManualPause()
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
