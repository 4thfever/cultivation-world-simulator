import { llmApi } from '@/api'
import { useUiStore, type SystemMenuContext } from '@/stores/ui'
import { storeToRefs } from 'pinia'
import { message } from '@/utils/discreteApi'
import { logError } from '@/utils/appError'
import i18n from '@/locales'

export function useSystemMenuFlow() {
  const uiStore = useUiStore()
  const translate = i18n.global.t

  const {
    systemMenuVisible: showMenu,
    systemMenuDefaultTab: menuDefaultTab,
    systemMenuClosable: canCloseMenu,
    systemMenuContext: menuContext,
  } = storeToRefs(uiStore)

  async function performStartupCheck(context: SystemMenuContext = 'game') {
    uiStore.openSystemMenu('start', true, context)

    try {
      const res = await llmApi.fetchStatus()
      if (!res.configured) {
        uiStore.openSystemMenu('llm', false, context)
        message.warning(translate('ui.llm_config_required_notice'))
      }
    } catch (e) {
      logError('SystemMenuFlow llm status', e)
      uiStore.openSystemMenu('llm', false, context)
      message.error(translate('ui.system_status_fetch_failed'))
    }
  }

  function openGameMenu() {
    uiStore.openSystemMenu('load', true, 'game')
  }

  function openSplashMenu(tab: typeof menuDefaultTab.value) {
    uiStore.openSystemMenu(tab, true, 'splash')
  }

  function openLLMConfig(context: SystemMenuContext = 'game') {
    uiStore.openSystemMenu('llm', false, context)
  }

  function handleLLMReady() {
    uiStore.setSystemMenuClosable(true)
    menuDefaultTab.value = 'start'
    message.success(translate('ui.llm_ready_start_game'))
  }

  function handleMenuClose() {
    if (canCloseMenu.value) {
      uiStore.closeSystemMenu()
    }
  }

  function switchTab(tab: typeof menuDefaultTab.value) {
    menuDefaultTab.value = tab
  }

  return {
    showMenu,
    menuDefaultTab,
    menuContext,
    canCloseMenu,
    performStartupCheck,
    openGameMenu,
    openSplashMenu,
    openLLMConfig,
    handleLLMReady,
    handleMenuClose,
    switchTab,
  }
}
