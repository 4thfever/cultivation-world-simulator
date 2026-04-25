import { computed, onMounted, ref, watch, type Ref } from 'vue'
import { useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import { systemApi } from '@/api'
import { useUiStore } from '@/stores/ui'
import { useWorldStore } from '@/stores/world'
import type { SaveFileDTO } from '@/types/api'

interface UseSaveLoadPanelOptions {
  mode: Ref<'save' | 'load'>
  close: () => void
}

export function useSaveLoadPanel(options: UseSaveLoadPanelOptions) {
  const { t } = useI18n()
  const worldStore = useWorldStore()
  const uiStore = useUiStore()
  const message = useMessage()

  const loading = ref(false)
  const saves = ref<SaveFileDTO[]>([])
  const showSaveModal = ref(false)
  const saveName = ref('')
  const saving = ref(false)

  const nameError = computed(() => {
    if (!saveName.value) return ''
    if (saveName.value.length > 50) {
      return t('save_load.name_too_long')
    }
    const pattern = /^[\w\u4e00-\u9fff]+$/
    if (!pattern.test(saveName.value)) {
      return t('save_load.name_invalid_chars')
    }
    return ''
  })

  async function fetchSaves() {
    loading.value = true
    try {
      saves.value = await systemApi.fetchSaves()
    } catch {
      message.error(t('save_load.fetch_failed'))
    } finally {
      loading.value = false
    }
  }

  function openSaveModal() {
    saveName.value = ''
    showSaveModal.value = true
  }

  async function handleQuickSave() {
    saving.value = true
    try {
      const res = await systemApi.saveGame()
      message.success(t('save_load.save_success', { filename: res.filename }))
      await fetchSaves()
    } catch {
      message.error(t('save_load.save_failed'))
    } finally {
      saving.value = false
    }
  }

  async function handleSaveWithName() {
    if (nameError.value) return

    saving.value = true
    try {
      const customName = saveName.value.trim() || undefined
      const res = await systemApi.saveGame(customName)
      message.success(t('save_load.save_success', { filename: res.filename }))
      showSaveModal.value = false
      saveName.value = ''
      await fetchSaves()
    } catch {
      message.error(t('save_load.save_failed'))
    } finally {
      saving.value = false
    }
  }

  async function handleLoad(filename: string) {
    if (!confirm(t('save_load.load_confirm', { filename }))) return

    loading.value = true
    try {
      await systemApi.loadGame(filename)
      worldStore.reset()
      uiStore.clearSelection()
      await worldStore.initialize()
      message.success(t('save_load.load_success'))
      options.close()
    } catch {
      message.error(t('save_load.load_failed'))
    } finally {
      loading.value = false
    }
  }

  async function handleDelete(filename: string) {
    if (!confirm(t('save_load.delete_confirm', { filename }))) return

    loading.value = true
    try {
      await systemApi.deleteSave(filename)
      message.success(t('save_load.delete_success'))
      await fetchSaves()
    } catch {
      message.error(t('save_load.delete_failed'))
    } finally {
      loading.value = false
    }
  }

  function formatSaveTime(isoTime: string): string {
    if (!isoTime) return ''
    try {
      const date = new Date(isoTime)
      return date.toLocaleString()
    } catch {
      return isoTime
    }
  }

  function getSaveDisplayName(save: SaveFileDTO): string {
    if (save.custom_name) {
      return save.custom_name
    }
    return save.filename?.replace('.json', '') || ''
  }

  watch(() => options.mode.value, () => {
    void fetchSaves()
  })

  onMounted(() => {
    void fetchSaves()
  })

  return {
    loading,
    saves,
    showSaveModal,
    saveName,
    saving,
    nameError,
    fetchSaves,
    openSaveModal,
    handleQuickSave,
    handleSaveWithName,
    handleLoad,
    handleDelete,
    formatSaveTime,
    getSaveDisplayName,
  }
}
