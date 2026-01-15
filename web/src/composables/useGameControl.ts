import { ref, watch, onMounted, type Ref } from 'vue'
import { llmApi } from '@/api'
import { useUiStore } from '@/stores/ui'
import { useSystemStore } from '@/stores/system'
import { message } from '@/utils/discreteApi'
import { storeToRefs } from 'pinia'

export function useGameControl(gameInitialized: Ref<boolean>) {
  const uiStore = useUiStore()
  const systemStore = useSystemStore()
  
  const { isManualPaused } = storeToRefs(systemStore)
  const showMenu = ref(false)
  const menuDefaultTab = ref<'save' | 'load' | 'create' | 'delete' | 'llm' | 'start'>('load')
  const canCloseMenu = ref(true)

  // 监听菜单状态和手动暂停状态，控制游戏暂停/继续
  watch([showMenu, isManualPaused], ([menuVisible, manualPaused]) => {
    // 只在游戏已准备好时控制暂停
    if (!gameInitialized.value) return
    
    if (menuVisible || manualPaused) {
      // 如果不是因为菜单打开而暂停（即用户手动暂停），则不需额外操作，因为状态已经在 store 里了
      // 但如果是菜单打开导致需要暂停，我们需要调用 pause
      if (menuVisible && !manualPaused) {
         systemStore.pause().catch(console.error)
      } else if (!menuVisible && !manualPaused) {
         // 菜单关闭且非手动暂停 -> 恢复
         systemStore.resume().catch(console.error)
      } else if (manualPaused) {
         // 只要是手动暂停，就确保是暂停状态
         systemStore.pause().catch(console.error)
      }
    } else {
      systemStore.resume().catch(console.error)
    }
  })

  // 优化：简化 Watch 逻辑
  // 核心规则：菜单打开 OR 手动暂停 => 必须暂停
  // 菜单关闭 AND 手动播放 => 恢复
  watch([showMenu], ([menuVisible]) => {
     if (!gameInitialized.value) return
     if (menuVisible) {
        systemStore.pause().catch(console.error)
     } else {
        // 关闭菜单时，如果不是手动暂停状态，则恢复
        if (!isManualPaused.value) {
            systemStore.resume().catch(console.error)
        }
     }
  })
  
  // Watch 手动暂停状态的变化，同步到后端
  watch(isManualPaused, (val) => {
      if (!gameInitialized.value) return
      if (val) systemStore.pause().catch(console.error)
      else if (!showMenu.value) systemStore.resume().catch(console.error)
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
                showMenu.value = false
            }
        } else {
            // 打开菜单
            showMenu.value = true
            menuDefaultTab.value = 'load'
        }
      }
    }
  }

  // LLM 相关控制逻辑
  async function performStartupCheck() {
    // 乐观设置：先假设可以进入开始页面并打开菜单
    showMenu.value = true
    menuDefaultTab.value = 'start'
    canCloseMenu.value = true

    try {
      const res = await llmApi.fetchStatus()
      
      if (!res.configured) {
        // 未配置 -> 强制进入 LLM 配置，禁止关闭
        menuDefaultTab.value = 'llm'
        canCloseMenu.value = false
        message.warning('检测到 LLM 未配置，请先完成设置')
      } else {
        // 已配置 -> 验证连通性
        try {
          const configRes = await llmApi.fetchConfig()
          await llmApi.testConnection(configRes)
          
          // 测试通过 -> 保持在 start 页面即可
        } catch (connErr) {
          // 连接失败 -> 强制进入配置
          console.error('LLM Connection check failed:', connErr)
          menuDefaultTab.value = 'llm'
          canCloseMenu.value = false
          message.error('LLM 连接测试失败，请重新配置')
        }
      }
    } catch (e) {
      console.error('Failed to check LLM status:', e)
      // Fallback
      menuDefaultTab.value = 'llm'
      canCloseMenu.value = false
      message.error('无法获取系统状态')
    }
  }

  function handleLLMReady() {
    canCloseMenu.value = true
    menuDefaultTab.value = 'start'
    message.success('LLM 配置成功，请开始游戏')
  }

  function handleMenuClose() {
    if (canCloseMenu.value) {
        showMenu.value = false
    }
  }

  function toggleManualPause() {
    systemStore.togglePause()
  }

  function openLLMConfig() {
    menuDefaultTab.value = 'llm'
    showMenu.value = true
  }

  onMounted(() => {
    // 暴露给全局以便 socket store 可以调用
    ;(window as any).__openLLMConfig = openLLMConfig
  })

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
