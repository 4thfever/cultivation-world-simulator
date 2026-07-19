import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDialog, useMessage } from 'naive-ui'
import { avatarApi, type SimpleAvatarDTO } from '@/api'
import { useAvatarStore } from '@/stores/avatar'
import { useWorldStore } from '@/stores/world'
import { useUiStore } from '@/stores/ui'
import { toErrorMessage } from '@/utils/appError'

type ConfirmDelete = (message: string) => boolean

export function useDeleteAvatarPanel(confirmDelete?: ConfirmDelete) {
  const avatarStore = useAvatarStore()
  const worldStore = useWorldStore()
  const uiStore = useUiStore()
  const message = useMessage()
  const dialog = useDialog()
  const { t } = useI18n()
  const isFetchingList = ref(false)
  const deletingAvatarId = ref<string | null>(null)
  const avatarList = ref<SimpleAvatarDTO[]>([])
  const avatarSearch = ref('')
  let listRequestId = 0

  function uiKey(path: string): string {
    return `ui.delete_avatar.${path}`
  }

  const filteredAvatars = computed(() => {
    if (!avatarSearch.value) return avatarList.value
    return avatarList.value.filter(avatar => avatar.name.includes(avatarSearch.value))
  })

  async function fetchAvatarList() {
    const requestId = ++listRequestId
    isFetchingList.value = true
    try {
      const avatars = await avatarApi.fetchAvatarList()
      if (requestId === listRequestId) {
        avatarList.value = avatars
      }
    } catch {
      if (requestId === listRequestId) {
        message.error(t(uiKey('fetch_failed')))
      }
    } finally {
      if (requestId === listRequestId) {
        isFetchingList.value = false
      }
    }
  }

  async function deleteAvatar(id: string) {
    if (deletingAvatarId.value) return

    // Do not let a list request started before this mutation restore the
    // deleted avatar after the command succeeds.
    listRequestId++
    isFetchingList.value = false
    deletingAvatarId.value = id
    try {
      const response = await avatarApi.deleteAvatar(id)
      worldStore.acceptMutationRevision(response.world_revision)
      avatarStore.removeAvatar(id)
      avatarList.value = avatarList.value.filter(avatar => avatar.id !== id)
      if (uiStore.selectedTarget?.type === 'avatar' && uiStore.selectedTarget.id === id) {
        uiStore.clearSelection()
      }
      message.success(t(uiKey('delete_success')))
    } catch (error) {
      message.error(toErrorMessage(error, t(uiKey('delete_failed'))))
    } finally {
      deletingAvatarId.value = null
    }
  }

  function handleDeleteAvatar(id: string, name: string) {
    const confirmation = t(uiKey('delete_confirm'), { name })
    if (confirmDelete) {
      if (confirmDelete(confirmation)) {
        return deleteAvatar(id)
      }
      return
    }

    dialog.warning({
      content: confirmation,
      positiveText: t('save_load.delete'),
      negativeText: t('common.cancel'),
      onPositiveClick: () => deleteAvatar(id),
    })
  }

  onMounted(() => {
    void fetchAvatarList()
  })

  watch(
    () => worldStore.avatarDirectoryRevision,
    () => {
      void fetchAvatarList()
    },
  )

  return {
    isFetchingList,
    deletingAvatarId,
    avatarSearch,
    filteredAvatars,
    uiKey,
    fetchAvatarList,
    handleDeleteAvatar,
  }
}
