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
  const menuDefaultTab = ref<'save' | 'load' | 'create' | 'delete' | 'llm' | 'start' | 'settings' | 'other'>('load')
  const canCloseMenu = ref(true)

  // 统一的暂停控制逻辑：
  // - 菜单打开时：暂停后端（不影响 isManualPaused）
  // - 菜单关闭时：如果没有手动暂停，恢复后端
  watch(showMenu, (menuVisible) => {
    if (!gameInitialized.value) return
    
    if (menuVisible) {
      // 菜单打开，暂停后端
      systemStore.pause().catch(console.error)
    } else {
      // 菜单关闭，只有在非手动暂停时才恢复
      if (!isManualPaused.value) {
        systemStore.resume().catch(console.error)
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
