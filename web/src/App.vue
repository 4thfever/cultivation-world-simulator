<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { NConfigProvider, darkTheme, NMessageProvider, NDialogProvider } from 'naive-ui'
import { systemApi } from './api/modules/system'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Components
import SplashLayer from './components/SplashLayer.vue'
import GameCanvas from './components/game/GameCanvas.vue'
import InfoPanelContainer from './components/game/panels/info/InfoPanelContainer.vue'
import StatusBar from './components/layout/StatusBar.vue'
import EventPanel from './components/game/panels/EventPanel.vue'
import SystemMenu from './components/SystemMenu.vue'
import LoadingOverlay from './components/LoadingOverlay.vue'

// Composables
import { useGameInit } from './composables/useGameInit'
import { useGameControl } from './composables/useGameControl'
import { useAudio } from './composables/useAudio'
import { useBgm } from './composables/useBgm'
import { useSidebarResize } from './composables/useSidebarResize'
import { useAppBootFlow } from './composables/useAppBootFlow'

// Stores
import { useUiStore } from './stores/ui'
import { useSettingStore } from './stores/setting'
import { useSystemStore } from './stores/system'

const uiStore = useUiStore()
const settingStore = useSettingStore()
const systemStore = useSystemStore()

// Sidebar resizer 状态
const { sidebarWidth, isResizing, onResizerMouseDown } = useSidebarResize()

// 1. 游戏初始化逻辑
const { 
  initStatus, 
  gameInitialized, 
  showLoading,
} = useGameInit()

// 2. 游戏控制逻辑
// 依赖 gameInitialized 状态来决定是否允许暂停等
const {
  showMenu,
  isManualPaused,
  menuDefaultTab,
  canCloseMenu,
  handleKeydown: controlHandleKeydown,
  performStartupCheck,
  handleLLMReady,
  handleMenuClose,
  toggleManualPause
} = useGameControl(gameInitialized)

const {
  showSplash,
  isAppReady,
  shouldBlockControls,
  handleSplashNavigate,
  handleMenuCloseWrapper,
  returnToSplash,
} = useAppBootFlow({
  initStatus,
  gameInitialized,
  showLoading,
  showMenu,
  menuDefaultTab,
  isManualPaused,
  performStartupCheck,
  handleMenuClose,
  onGameBgmStart: () => useBgm().play('map'),
  onResumeGame: () => systemStore.resume(),
})

// 事件处理
function onKeydown(e: KeyboardEvent) {
  if (shouldBlockControls.value) return
  controlHandleKeydown(e)
}

function handleSelection(target: { type: 'avatar' | 'region'; id: string; name?: string }) {
  uiStore.select(target.type, target.id)
}

async function handleSplashAction(key: string) {
  if (key === 'exit') {
    try {
      await systemApi.shutdown()
      window.close()
      document.body.innerHTML = `<div style="color:white; display:flex; justify-content:center; align-items:center; height:100vh; background:black; font-size:24px;">${t('game.controls.closed_msg')}</div>`
    } catch (e) {
      console.error('Shutdown failed', e)
    }
    return
  }

  if (key === 'start' || key === 'load' || key === 'settings' || key === 'about') {
    handleSplashNavigate(key)
  }
}

async function handleReturnToMain() {
  try {
    await systemApi.resetGame()
    returnToSplash()
  } catch (e) {
    console.error('Reset game failed', e)
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  settingStore.hydrate().finally(() => {
    useAudio().init()
    useBgm().init() // 确保 BGM 系统在 App 层级初始化，避免 Watcher 被子组件卸载
  })
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <n-config-provider :theme="darkTheme">
    <n-dialog-provider>
      <n-message-provider>
        <!-- 获取到后端状态和 settings 前显示纯黑，避免启动阶段界面闪烁 -->
      <div v-if="!isAppReady || !settingStore.hydrated" class="app-layout" style="background: #000;"></div>
      
      <template v-else>
        <SplashLayer 
          v-if="showSplash" 
          @action="handleSplashAction"
        />
        
        <!-- Loading Overlay - 盖在游戏上面 -->
        <!-- 当后端已经 ready 但前端仍在收尾初始化时，不显示额外 Loading 以减少界面跳变。-->
        <LoadingOverlay 
          v-if="!showSplash && showLoading && initStatus?.status !== 'ready'"
          :status="initStatus"
        />

        <!-- Game UI - 始终渲染 -->
        <div v-if="!showSplash && (!showLoading || initStatus?.status === 'ready')" class="app-layout">
        <StatusBar />
        
        <div class="main-content">
          <div class="map-container">
            <!-- 顶部控制栏 -->
            <div class="top-controls">
              <!-- 暂停/播放按钮 -->
              <button class="control-btn pause-toggle" @click="toggleManualPause" :title="isManualPaused ? t('game.controls.resume') : t('game.controls.pause')">
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
              <div class="pause-text">{{ t('game.controls.paused') }}</div>
            </div>

            <GameCanvas
              :sidebar-width="sidebarWidth"
              @avatarSelected="handleSelection"
              @regionSelected="handleSelection"
            />
            <InfoPanelContainer />
          </div>
          <div
            class="sidebar-resizer"
            :class="{ 'is-resizing': isResizing }"
            @mousedown="onResizerMouseDown"
          ></div>
          <aside class="sidebar" :style="{ width: sidebarWidth + 'px' }">
            <EventPanel />
          </aside>
        </div>

        <SystemMenu 
          :visible="showMenu"
          :default-tab="menuDefaultTab"
          :game-initialized="gameInitialized"
          :closable="canCloseMenu"
          @close="handleMenuCloseWrapper"
          @llm-ready="handleLLMReady"
          @return-to-main="handleReturnToMain"
          @exit-game="() => handleSplashAction('exit')"
        />
      </div>
      </template>
      </n-message-provider>
    </n-dialog-provider>
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

.sidebar-resizer {
  width: 4px;
  background: transparent;
  cursor: col-resize;
  transition: background 0.15s;
  flex-shrink: 0;
}

.sidebar-resizer:hover,
.sidebar-resizer.is-resizing {
  background: #555;
}

.sidebar {
  background: #181818;
  border-left: 1px solid #333;
  display: flex;
  flex-direction: column;
  z-index: 20;
  flex-shrink: 0;
}
</style>
