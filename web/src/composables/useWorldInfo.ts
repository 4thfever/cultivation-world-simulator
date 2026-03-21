import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { loadWorldInfoRows, translateWorldInfoRows, type WorldInfoEntry, type WorldInfoCsvRow } from '../utils/worldInfo'

export function useWorldInfo() {
  const { t } = useI18n()
  const rows = ref<WorldInfoCsvRow[]>([])
  const loading = ref(false)
  const error = ref<Error | null>(null)

  const entries = computed<WorldInfoEntry[]>(() => translateWorldInfoRows(rows.value, t))

  async function ensureLoaded() {
    if (rows.value.length > 0 || loading.value) {
      return
    }

    loading.value = true
    error.value = null
    try {
      rows.value = loadWorldInfoRows()
    } catch (err) {
      error.value = err instanceof Error ? err : new Error(String(err))
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    void ensureLoaded()
  })

  return {
    entries,
    loading,
    error,
    ensureLoaded,
  }
}
