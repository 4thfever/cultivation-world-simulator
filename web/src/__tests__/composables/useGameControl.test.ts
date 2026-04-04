import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, ref } from 'vue'
import { useUiStore } from '@/stores/ui'
import { useSystemStore } from '@/stores/system'
import { useGameControl } from '@/composables/useGameControl'

const createTestComponent = () => {
  const showMenu = ref(false)
  const canCloseMenu = ref(true)
  const gameInitialized = ref(false)
  const openGameMenu = vi.fn(() => {
    showMenu.value = true
  })
  const closeMenu = vi.fn(() => {
    showMenu.value = false
  })

  const component = defineComponent({
    setup() {
      return useGameControl({
        gameInitialized,
        showMenu,
        canCloseMenu,
        openGameMenu,
        closeMenu,
      })
    },
    template: '<div></div>',
  })

  return { component, showMenu, canCloseMenu, gameInitialized, openGameMenu, closeMenu }
}

describe('useGameControl', () => {
  let uiStore: ReturnType<typeof useUiStore>
  let systemStore: ReturnType<typeof useSystemStore>

  beforeEach(() => {
    uiStore = useUiStore()
    systemStore = useSystemStore()
    vi.clearAllMocks()
  })

  it('clears selection when Escape pressed and target selected', () => {
    const { component } = createTestComponent()
    const wrapper = mount(component)

    uiStore.selectedTarget = { type: 'avatar', id: '123' }

    wrapper.vm.handleKeydown(new KeyboardEvent('keydown', { key: 'Escape' }))

    expect(uiStore.selectedTarget).toBeNull()
    wrapper.unmount()
  })

  it('opens game menu when Escape pressed without selection', () => {
    const { component, gameInitialized, openGameMenu } = createTestComponent()
    gameInitialized.value = true
    const wrapper = mount(component)

    wrapper.vm.handleKeydown(new KeyboardEvent('keydown', { key: 'Escape' }))

    expect(openGameMenu).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('closes menu when Escape pressed and menu is closable', () => {
    const { component, gameInitialized, showMenu, canCloseMenu, closeMenu } = createTestComponent()
    gameInitialized.value = true
    showMenu.value = true
    canCloseMenu.value = true
    const wrapper = mount(component)

    wrapper.vm.handleKeydown(new KeyboardEvent('keydown', { key: 'Escape' }))

    expect(closeMenu).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('does not close menu when Escape pressed and menu is not closable', () => {
    const { component, gameInitialized, showMenu, canCloseMenu, closeMenu } = createTestComponent()
    gameInitialized.value = true
    showMenu.value = true
    canCloseMenu.value = false
    const wrapper = mount(component)

    wrapper.vm.handleKeydown(new KeyboardEvent('keydown', { key: 'Escape' }))

    expect(closeMenu).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('pauses and resumes backend when menu visibility changes after initialization', async () => {
    const pauseSpy = vi.spyOn(systemStore, 'pause').mockResolvedValue(undefined)
    const resumeSpy = vi.spyOn(systemStore, 'resume').mockResolvedValue(undefined)
    const { component, gameInitialized, showMenu } = createTestComponent()
    gameInitialized.value = true
    systemStore.isManualPaused = false
    const wrapper = mount(component)

    showMenu.value = true
    await Promise.resolve()
    showMenu.value = false
    await Promise.resolve()

    expect(pauseSpy).toHaveBeenCalledTimes(1)
    expect(resumeSpy).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('toggles manual pause via system store', () => {
    const togglePauseSpy = vi.spyOn(systemStore, 'togglePause').mockResolvedValue(undefined)
    const { component } = createTestComponent()
    const wrapper = mount(component)

    wrapper.vm.toggleManualPause()

    expect(togglePauseSpy).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })
})
