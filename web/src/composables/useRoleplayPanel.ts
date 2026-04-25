import { computed, watch } from 'vue'
import type { ComposerTranslation } from 'vue-i18n'
import { useRoleplayStore } from '@/stores/roleplay'
import { useUiStore } from '@/stores/ui'

export interface RoleplayPanelAvatar {
  id: string
}

export function useRoleplayPanel(
  avatar: () => RoleplayPanelAvatar,
  t: ComposerTranslation,
) {
  const roleplayStore = useRoleplayStore()
  const uiStore = useUiStore()

  const session = computed(() => roleplayStore.session)
  const currentAvatarId = computed(() => avatar().id)
  const controlledAvatarId = computed(() => session.value.controlled_avatar_id ?? '')
  const isCurrentAvatarControlled = computed(() => controlledAvatarId.value === currentAvatarId.value)
  const isAnotherAvatarControlled = computed(() => !!controlledAvatarId.value && !isCurrentAvatarControlled.value)
  const controlledAvatarName = computed(() => {
    const context = session.value.last_prompt_context ?? {}
    const rawName = typeof context.avatar_name === 'string' ? context.avatar_name : ''
    return rawName || controlledAvatarId.value || t('game.roleplay.fallback.avatar_name')
  })

  async function refreshRoleplayState() {
    await roleplayStore.fetchSession()
  }

  async function handleStartRoleplay() {
    await roleplayStore.startRoleplay(currentAvatarId.value)
  }

  async function handleStopRoleplay() {
    await roleplayStore.stopRoleplay(currentAvatarId.value)
  }

  function handleGoToControlledAvatar() {
    if (controlledAvatarId.value) {
      uiStore.select('avatar', controlledAvatarId.value)
    }
  }

  watch(currentAvatarId, () => {
    void refreshRoleplayState()
  }, { immediate: true })

  return {
    roleplayStore,
    isCurrentAvatarControlled,
    isAnotherAvatarControlled,
    controlledAvatarName,
    handleStartRoleplay,
    handleStopRoleplay,
    handleGoToControlledAvatar,
    refreshRoleplayState,
  }
}
