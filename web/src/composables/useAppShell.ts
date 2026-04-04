import { computed, getCurrentScope, onScopeDispose, ref, watch, type Ref } from 'vue'
import type { InitStatusDTO } from '@/types/api'
import type { SystemMenuContext, SystemMenuTab } from '@/stores/ui'

interface UseAppShellOptions {
  settingsHydrated: Ref<boolean>
  initStatus: Ref<InitStatusDTO | null>
  gameInitialized: Ref<boolean>
  showLoading: Ref<boolean>
  showMenu: Ref<boolean>
  menuDefaultTab: Ref<SystemMenuTab>
  menuContext: Ref<SystemMenuContext>
  isManualPaused: Ref<boolean>
  performStartupCheck: (context?: SystemMenuContext) => void | Promise<void>
  handleMenuClose: () => void
  onGameBgmStart: () => void
  onResumeGame: () => Promise<void>
}

export type AppScene = 'boot' | 'splash' | 'initializing' | 'game'
type SplashActionKey = 'start' | 'load' | 'settings' | 'about'
const INITIAL_LOADING_GRACE_MS = 400

export function useAppShell(options: UseAppShellOptions) {
  const hasReceivedInitStatus = ref(false)
  const forcedScene = ref<AppScene | null>(null)
  const startupResolved = ref(false)
  let initialLoadingTimer: ReturnType<typeof setTimeout> | null = null

  function clearInitialLoadingTimer() {
    if (initialLoadingTimer) {
      clearTimeout(initialLoadingTimer)
      initialLoadingTimer = null
    }
  }

  function resolveStartup() {
    startupResolved.value = true
    clearInitialLoadingTimer()
  }

  const baseScene = computed<AppScene>(() => {
    if (!options.settingsHydrated.value || !hasReceivedInitStatus.value || !startupResolved.value) {
      return 'boot'
    }

    if (options.gameInitialized.value) {
      return 'game'
    }

    if (options.initStatus.value?.status && options.initStatus.value.status !== 'idle') {
      return 'initializing'
    }

    return 'splash'
  })

  const scene = computed<AppScene>(() => {
    if (baseScene.value === 'boot') {
      return 'boot'
    }

    return forcedScene.value ?? baseScene.value
  })

  const showLoadingOverlay = computed(() => {
    return scene.value === 'initializing'
      && options.showLoading.value
      && options.initStatus.value?.status !== 'ready'
  })

  const canRenderGameShell = computed(() => scene.value === 'game')
  const canRenderSplash = computed(() => scene.value === 'splash')
  const shouldBlockControls = computed(() => scene.value !== 'game' || showLoadingOverlay.value)

  watch(options.initStatus, (newVal) => {
    if (newVal) {
      hasReceivedInitStatus.value = true
    }
  }, { immediate: true })

  watch(
    [options.settingsHydrated, options.initStatus, options.gameInitialized],
    ([settingsHydrated, initStatus, gameInitialized]) => {
      if (!settingsHydrated || startupResolved.value) return
      if (gameInitialized) {
        resolveStartup()
        return
      }
      if (!initStatus) return

      if (initStatus.status === 'idle') {
        resolveStartup()
        return
      }

      if (!initialLoadingTimer) {
        initialLoadingTimer = setTimeout(() => {
          resolveStartup()
        }, INITIAL_LOADING_GRACE_MS)
      }
    },
    { immediate: true },
  )

  watch(options.initStatus, (newVal, oldVal) => {
    if (oldVal?.status !== 'ready' && newVal?.status === 'ready') {
      options.showMenu.value = false
    }
  })

  watch(options.gameInitialized, async (val) => {
    if (!val) return

    resolveStartup()
    forcedScene.value = null
    options.onGameBgmStart()
    options.isManualPaused.value = false
    await options.onResumeGame()
  }, { immediate: true })

  watch([baseScene, options.gameInitialized], ([nextBaseScene, initialized]) => {
    if (!forcedScene.value) return

    if (forcedScene.value === 'splash' && nextBaseScene === 'splash' && !initialized) {
      forcedScene.value = null
    }
  })

  function openSplashMenu(tab: SystemMenuTab) {
    options.menuDefaultTab.value = tab
    options.menuContext.value = 'splash'
    options.showMenu.value = true
  }

  function handleSplashNavigate(key: SplashActionKey) {
    forcedScene.value = null

    if (key === 'start') {
      resolveStartup()
      void options.performStartupCheck('splash')
      return
    }

    openSplashMenu(key)
  }

  function handleMenuCloseWrapper() {
    options.handleMenuClose()
  }

  function returnToSplash() {
    resolveStartup()
    forcedScene.value = 'splash'
    options.showMenu.value = false
    options.menuContext.value = 'splash'
  }

  if (getCurrentScope()) {
    onScopeDispose(() => {
      clearInitialLoadingTimer()
    })
  }

  return {
    scene,
    canRenderGameShell,
    canRenderSplash,
    showLoadingOverlay,
    shouldBlockControls,
    handleSplashNavigate,
    handleMenuCloseWrapper,
    returnToSplash,
  }
}
