import { describe, it, expect, vi, afterEach } from 'vitest'
import { ref } from 'vue'
import { useAppShell } from '@/composables/useAppShell'
import type { InitStatusDTO } from '@/types/api'
import type { SystemMenuContext, SystemMenuTab } from '@/stores/ui'

function makeStatus(overrides: Partial<InitStatusDTO> = {}): InitStatusDTO {
  return {
    status: 'idle',
    phase: 0,
    phase_name: '',
    progress: 0,
    elapsed_seconds: 0,
    error: null,
    llm_check_failed: false,
    llm_error_message: '',
    ...overrides,
  }
}

function createShell(overrides: Partial<Parameters<typeof useAppShell>[0]> = {}) {
  const settingsHydrated = ref(true)
  const initStatus = ref<InitStatusDTO | null>(null)
  const gameInitialized = ref(false)
  const showLoading = ref(false)
  const showMenu = ref(false)
  const menuDefaultTab = ref<SystemMenuTab>('load')
  const menuContext = ref<SystemMenuContext>('game')
  const isManualPaused = ref(true)
  const performStartupCheck = vi.fn()
  const handleMenuClose = vi.fn(() => {
    showMenu.value = false
    menuContext.value = 'game'
  })
  const onGameBgmStart = vi.fn()
  const onResumeGame = vi.fn().mockResolvedValue(undefined)

  const shell = useAppShell({
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
    onGameBgmStart,
    onResumeGame,
    ...overrides,
  })

  return {
    shell,
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
    onGameBgmStart,
    onResumeGame,
  }
}

describe('useAppShell', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('stays in boot scene until settings and init status are ready', async () => {
    const settingsHydrated = ref(false)
    const initStatus = ref<InitStatusDTO | null>(null)

    const { shell } = createShell({
      settingsHydrated,
      initStatus,
    })

    expect(shell.scene.value).toBe('boot')

    settingsHydrated.value = true
    await Promise.resolve()
    expect(shell.scene.value).toBe('boot')

    initStatus.value = makeStatus({ status: 'idle' })
    await Promise.resolve()
    expect(shell.scene.value).toBe('splash')
  })

  it('opens splash menu without leaving splash scene', async () => {
    const { shell, initStatus, showMenu, menuDefaultTab, menuContext } = createShell()

    initStatus.value = makeStatus({ status: 'idle' })
    await Promise.resolve()

    shell.handleSplashNavigate('settings')

    expect(shell.scene.value).toBe('splash')
    expect(showMenu.value).toBe(true)
    expect(menuDefaultTab.value).toBe('settings')
    expect(menuContext.value).toBe('splash')
  })

  it('routes splash start into startup check with splash context', async () => {
    const { shell, initStatus, performStartupCheck } = createShell()

    initStatus.value = makeStatus({ status: 'idle' })
    await Promise.resolve()

    shell.handleSplashNavigate('start')

    expect(performStartupCheck).toHaveBeenCalledWith('splash')
  })

  it('renders initializing before game and game after initialization completes', async () => {
    vi.useFakeTimers()
    const { shell, initStatus, showLoading, gameInitialized, onGameBgmStart, onResumeGame, isManualPaused } = createShell()

    initStatus.value = makeStatus({ status: 'in_progress' })
    showLoading.value = true
    await Promise.resolve()
    expect(shell.scene.value).toBe('boot')
    expect(shell.showLoadingOverlay.value).toBe(false)

    vi.advanceTimersByTime(450)
    await Promise.resolve()

    expect(shell.scene.value).toBe('initializing')
    expect(shell.showLoadingOverlay.value).toBe(true)
    expect(shell.canRenderGameShell.value).toBe(false)

    gameInitialized.value = true
    await Promise.resolve()

    expect(shell.scene.value).toBe('game')
    expect(onGameBgmStart).toHaveBeenCalledTimes(1)
    expect(onResumeGame).toHaveBeenCalledTimes(1)
    expect(isManualPaused.value).toBe(false)
  })

  it('does not flash loading when initial non-idle status quickly settles back to idle', async () => {
    vi.useFakeTimers()
    const { shell, initStatus, showLoading } = createShell()

    showLoading.value = true
    initStatus.value = makeStatus({ status: 'in_progress' })
    await Promise.resolve()

    expect(shell.scene.value).toBe('boot')
    expect(shell.showLoadingOverlay.value).toBe(false)

    initStatus.value = makeStatus({ status: 'idle' })
    await Promise.resolve()

    expect(shell.scene.value).toBe('splash')
    expect(shell.showLoadingOverlay.value).toBe(false)

    vi.advanceTimersByTime(450)
    await Promise.resolve()

    expect(shell.scene.value).toBe('splash')
    expect(shell.showLoadingOverlay.value).toBe(false)
  })

  it('returns to splash immediately after reset request', async () => {
    const { shell, initStatus, gameInitialized, showMenu } = createShell()

    initStatus.value = makeStatus({ status: 'ready' })
    gameInitialized.value = true
    showMenu.value = true
    await Promise.resolve()

    shell.returnToSplash()

    expect(shell.scene.value).toBe('splash')
    expect(showMenu.value).toBe(false)
  })
})
