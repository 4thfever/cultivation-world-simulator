<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { NConfigProvider, darkTheme, NMessageProvider } from 'naive-ui'
import { useWorldStore } from './stores/world'
import { useUiStore } from './stores/ui'
import { useGameSocket } from './composables/useGameSocket'
import { gameApi } from './api/game'

import GameCanvas from './components/game/GameCanvas.vue'
import InfoPanelContainer from './components/game/panels/info/InfoPanelContainer.vue'
import StatusBar from './components/layout/StatusBar.vue'
import EventPanel from './components/panels/EventPanel.vue'
import SystemMenu from './components/SystemMenu.vue'

// Composables
useGameSocket()

const worldStore = useWorldStore()
const uiStore = useUiStore()
const showMenu = ref(false)

onMounted(async () => {
  await worldStore.initialize()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

function handleKeydown(e: KeyboardEvent) {
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

// 监听菜单状态，控制游戏暂停/继续
watch(showMenu, (visible) => {
  if (visible) {
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
            <!-- 菜单按钮移动到这里，相对于地图区域定位 -->
            <button class="menu-toggle" @click="showMenu = true">
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
              </svg>
            </button>

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

.menu-toggle {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 100;
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
}

.menu-toggle:hover {
  background: rgba(0,0,0,0.8);
  border-color: #666;
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
