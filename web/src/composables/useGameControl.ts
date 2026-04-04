import { watch, type Ref } from 'vue'
import { useUiStore } from '@/stores/ui'
import { useSystemStore } from '@/stores/system'
import { logError } from '@/utils/appError'
import { storeToRefs } from 'pinia'

interface UseGameControlOptions {
  gameInitialized: Ref<boolean>
  showMenu: Ref<boolean>
  canCloseMenu: Ref<boolean>
  openGameMenu: () => void
  closeMenu: () => void
}

export function useGameControl(options: UseGameControlOptions) {
  const uiStore = useUiStore()
  const systemStore = useSystemStore()
  
  const { isManualPaused } = storeToRefs(systemStore)

  // 统一的暂停控制逻辑：
  // - 菜单打开时：暂停后端（不影响 isManualPaused）
  // - 菜单关闭时：如果没有手动暂停，恢复后端
  watch(options.showMenu, (menuVisible) => {
    if (!options.gameInitialized.value) return
    
    if (menuVisible) {
      systemStore.pause().catch((e) => logError('GameControl pause', e))
    } else {
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
        if (options.showMenu.value) {
          if (options.canCloseMenu.value) {
            options.closeMenu()
          }
        } else {
          options.openGameMenu()
        }
      }
    }
  }

  function toggleManualPause() {
    systemStore.togglePause()
  }

  return {
    isManualPaused,
    handleKeydown,
    toggleManualPause,
  }
}
