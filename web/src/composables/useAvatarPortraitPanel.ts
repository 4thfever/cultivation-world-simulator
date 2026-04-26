import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import { avatarApi } from '@/api'
import { useAvatarStore } from '@/stores/avatar'
import { getAvatarPortraitUrl } from '@/utils/assetUrls'
import { logError, toErrorMessage } from '@/utils/appError'

export interface AvatarPortraitPanelProps {
  avatarId: string
  gender: string
  currentPicId?: number | null
  visible: boolean
}

export function useAvatarPortraitPanel(
  props: AvatarPortraitPanelProps,
  emit: {
    (e: 'close'): void
    (e: 'updated'): void
  },
) {
  const { t } = useI18n()
  const message = useMessage()
  const avatarStore = useAvatarStore()

  const avatarMeta = ref<{ males: number[]; females: number[] } | null>(null)
  const isLoading = ref(false)
  const submitLoading = ref(false)
  const errorText = ref('')
  const selectedPicId = ref<number | null>(props.currentPicId ?? null)

  const availableAvatars = computed(() => {
    if (!avatarMeta.value) return []
    const normalizedGender = String(props.gender || '').toLowerCase()
    return normalizedGender === 'female' || normalizedGender === '女'
      ? avatarMeta.value.females
      : avatarMeta.value.males
  })

  const previewUrl = computed(() => getAvatarPortraitUrl(props.gender, selectedPicId.value))

  watch(
    () => props.currentPicId,
    value => {
      selectedPicId.value = value ?? null
    },
    { immediate: true },
  )

  watch(
    () => props.visible,
    async visible => {
      errorText.value = ''
      if (!visible || avatarMeta.value || isLoading.value) return
      isLoading.value = true
      try {
        avatarMeta.value = await avatarApi.fetchAvatarMeta()
      } catch (error) {
        logError('AvatarPortraitPanel.fetchAvatarMeta', error)
        errorText.value = toErrorMessage(error, t('game.info_panel.avatar.portrait.load_failed'))
      } finally {
        isLoading.value = false
      }
    },
    { immediate: true },
  )

  async function handleApply() {
    if (!selectedPicId.value || submitLoading.value) return
    submitLoading.value = true
    errorText.value = ''
    try {
      await avatarApi.updateAvatarPortrait({
        avatar_id: props.avatarId,
        pic_id: selectedPicId.value,
      })
      avatarStore.updateAvatarSummary(props.avatarId, { pic_id: selectedPicId.value })
      message.success(t('game.info_panel.avatar.portrait.apply_success'))
      emit('updated')
      emit('close')
    } catch (error) {
      logError('AvatarPortraitPanel.handleApply', error)
      errorText.value = toErrorMessage(error, t('game.info_panel.avatar.portrait.apply_failed'))
    } finally {
      submitLoading.value = false
    }
  }

  return {
    isLoading,
    submitLoading,
    errorText,
    selectedPicId,
    availableAvatars,
    previewUrl,
    handleApply,
    getAvatarPortraitUrl,
  }
}
