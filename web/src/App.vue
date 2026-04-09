<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
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
import menuIcon from '@/assets/icons/ui/lucide/menu.svg'
import playIcon from '@/assets/icons/ui/lucide/play.svg'
import pauseIcon from '@/assets/icons/ui/lucide/pause.svg'

// Composables
import { useGameInit } from './composables/useGameInit'
import { useGameControl } from './composables/useGameControl'
import { useAudio } from './composables/useAudio'
import { useBgm } from './composables/useBgm'
import { useSidebarResize } from './composables/useSidebarResize'
import { useAppShell } from './composables/useAppShell'
import { useSystemMenuFlow } from './composables/useSystemMenuFlow'
import { logError } from './utils/appError'

// Stores
import { useUiStore } from './stores/ui'
import { useSettingStore } from './stores/setting'
import { useSystemStore } from './stores/system'

const uiStore = useUiStore()
const settingStore = useSettingStore()
const systemStore = useSystemStore()

// Sidebar resizer 状态
const { sidebarWidth, isResizing, onResizerMouseDown } = useSidebarResize()

function syncLayoutCssVars(width: number) {
  document.documentElement.style.setProperty('--cws-sidebar-width', `${width}px`)
}

// 1. 游戏初始化逻辑
const { 
  initStatus, 
  gameInitialized, 
  showLoading,
} = useGameInit()

const {
  showMenu,
  menuDefaultTab,
  menuContext,
  canCloseMenu,
  performStartupCheck,
  openGameMenu,
  handleLLMReady,
  handleMenuClose,
} = useSystemMenuFlow()

const {
  isManualPaused,
  handleKeydown: controlHandleKeydown,
  toggleManualPause
} = useGameControl({
  gameInitialized,
  showMenu,
  canCloseMenu,
  openGameMenu,
  closeMenu: handleMenuClose,
})

const settingsHydrated = computed(() => settingStore.hydrated)

const {
  scene,
  canRenderGameShell,
  canRenderSplash,
  showLoadingOverlay,
  shouldBlockControls,
  handleSplashNavigate,
  handleMenuCloseWrapper,
  returnToSplash,
} = useAppShell({
  settingsHydrated,
  initStatus,
  gameInitialized,
  showLoading,
  showMenu,
  menuDefaultTab,
  menuContext,
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
      logError('App shutdown', e)
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
    logError('App reset game', e)
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  syncLayoutCssVars(sidebarWidth.value)
  settingStore.hydrate().finally(() => {
    useAudio().init()
    useBgm().init() // 确保 BGM 系统在 App 层级初始化，避免 Watcher 被子组件卸载
  })
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.documentElement.style.removeProperty('--cws-sidebar-width')
})

watch(sidebarWidth, width => {
  syncLayoutCssVars(width)
})
</script>

<template>
  <n-config-provider :theme="darkTheme">
    <n-dialog-provider>
      <n-message-provider>
        <div v-if="scene === 'boot'" class="app-layout app-layout--shell"></div>

        <SplashLayer 
          v-else-if="canRenderSplash" 
          @action="handleSplashAction"
        />

        <div v-else-if="scene === 'initializing'" class="app-layout app-layout--shell"></div>

        <div v-else-if="canRenderGameShell" class="app-layout">
          <StatusBar />
          
          <div class="main-content">
            <div class="map-container">
              <!-- 顶部控制栏 -->
              <div class="top-controls">
                <!-- 暂停/播放按钮 -->
                <button class="control-btn pause-toggle" @click="toggleManualPause" :title="isManualPaused ? t('game.controls.resume') : t('game.controls.pause')">
                  <span
                    class="control-btn-icon"
                    :style="{ '--icon-url': `url(${isManualPaused ? playIcon : pauseIcon})` }"
                    aria-hidden="true"
                  ></span>
                </button>

                <!-- 菜单按钮 -->
                <button class="control-btn menu-toggle" @click="openGameMenu()">
                  <span
                    class="control-btn-icon"
                    :style="{ '--icon-url': `url(${menuIcon})` }"
                    aria-hidden="true"
                  ></span>
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

        <LoadingOverlay 
          v-if="showLoadingOverlay"
          :status="initStatus"
        />
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

.app-layout--shell {
  background: #000;
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

.control-btn-icon {
  width: 18px;
  height: 18px;
  display: inline-block;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
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
