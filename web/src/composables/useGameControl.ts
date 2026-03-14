import { watch, type Ref } from 'vue'
import { llmApi } from '@/api'
import { useUiStore } from '@/stores/ui'
import { useSystemStore } from '@/stores/system'
import { message } from '@/utils/discreteApi'
import { logError } from '@/utils/appError'
import { storeToRefs } from 'pinia'

export function useGameControl(gameInitialized: Ref<boolean>) {
  const uiStore = useUiStore()
  const systemStore = useSystemStore()
  
  const { isManualPaused } = storeToRefs(systemStore)
  const { systemMenuVisible: showMenu, systemMenuDefaultTab: menuDefaultTab, systemMenuClosable: canCloseMenu } = storeToRefs(uiStore)

  // 统一的暂停控制逻辑：
  // - 菜单打开时：暂停后端（不影响 isManualPaused）
  // - 菜单关闭时：如果没有手动暂停，恢复后端
  watch(showMenu, (menuVisible) => {
    if (!gameInitialized.value) return
    
    if (menuVisible) {
      // 菜单打开，暂停后端
      systemStore.pause().catch((e) => logError('GameControl pause', e))
    } else {
      // 菜单关闭，只有在非手动暂停时才恢复
      if (!isManualPaused.value) {
        systemStore.resume().catch((e) => logError('GameControl resume', e))
      }
    }
  })

  // 快捷键处理
  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      if (uiStore.selectedTarget) {
        uiStore.clearSelection()
      } else {
        if (showMenu.value) {
            // 如果菜单打开，尝试关闭（如果允许）
            if (canCloseMenu.value) {
                uiStore.closeSystemMenu()
            }
        } else {
            // 打开菜单
            uiStore.openSystemMenu('load', true)
        }
      }
    }
  }

  // LLM 相关控制逻辑
  async function performStartupCheck() {
    // 乐观设置：先假设可以进入开始页面并打开菜单
    uiStore.openSystemMenu('start', true)

    try {
      const res = await llmApi.fetchStatus()
      
      if (!res.configured) {
        // 未配置 -> 强制进入 LLM 配置，禁止关闭
        uiStore.openSystemMenu('llm', false)
        message.warning('检测到 LLM 未配置，请先完成设置')
      }
    } catch (e) {
      logError('GameControl llm status', e)
      // Fallback
      uiStore.openSystemMenu('llm', false)
      message.error('无法获取系统状态')
    }
  }

  function handleLLMReady() {
    uiStore.setSystemMenuClosable(true)
    menuDefaultTab.value = 'start'
    message.success('LLM 配置成功，请开始游戏')
  }

  function handleMenuClose() {
    if (canCloseMenu.value) {
        uiStore.closeSystemMenu()
    }
  }

  function toggleManualPause() {
    systemStore.togglePause()
  }

  function openLLMConfig() {
    uiStore.openSystemMenu('llm', false)
  }

  return {
    showMenu,
    isManualPaused,
    menuDefaultTab,
    canCloseMenu,
    
    handleKeydown,
    performStartupCheck,
    handleLLMReady,
    handleMenuClose,
    toggleManualPause,
    openLLMConfig
  }
}
