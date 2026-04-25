import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import { avatarApi, type SimpleAvatarDTO } from '@/api'
import { useWorldStore } from '@/stores/world'

export function useDeleteAvatarPanel(confirmDelete: (message: string) => boolean = window.confirm) {
  const worldStore = useWorldStore()
  const message = useMessage()
  const { t } = useI18n()
  const loading = ref(false)
  const avatarList = ref<SimpleAvatarDTO[]>([])
  const avatarSearch = ref('')

  function uiKey(path: string): string {
    return `ui.delete_avatar.${path}`
  }

  const filteredAvatars = computed(() => {
    if (!avatarSearch.value) return avatarList.value
    return avatarList.value.filter(avatar => avatar.name.includes(avatarSearch.value))
  })

  async function fetchAvatarList() {
    loading.value = true
    try {
      avatarList.value = await avatarApi.fetchAvatarList()
    } catch {
      message.error(t(uiKey('fetch_failed')))
    } finally {
      loading.value = false
    }
  }

  async function handleDeleteAvatar(id: string, name: string) {
    if (!confirmDelete(t(uiKey('delete_confirm'), { name }))) return

    loading.value = true
    try {
      await avatarApi.deleteAvatar(id)
      message.success(t(uiKey('delete_success')))
      await Promise.all([
        fetchAvatarList(),
        worldStore.fetchState ? worldStore.fetchState() : Promise.resolve(),
      ])
    } catch {
      message.error(t(uiKey('delete_failed')))
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    void fetchAvatarList()
  })

  return {
    loading,
    avatarSearch,
    filteredAvatars,
    uiKey,
    fetchAvatarList,
    handleDeleteAvatar,
  }
}
