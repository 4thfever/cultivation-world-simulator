import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { worldApi } from '@/api/modules/world'
import type { WorldSecretOverviewResponseDTO } from '@/types/api'
import { logWarn } from '@/utils/appError'

export const useWorldSecretStore = defineStore('worldSecret', () => {
  const overview = ref<WorldSecretOverviewResponseDTO | null>(null)
  const loading = ref(false)
  const loaded = ref(false)

  const activeSecret = computed(() => overview.value?.active_secret ?? null)
  const isNone = computed(() => !activeSecret.value || activeSecret.value.id === 'none')

  async function refreshOverview() {
    if (loading.value) return
    loading.value = true
    try {
      overview.value = await worldApi.fetchWorldSecretOverview()
      loaded.value = true
    } catch (e) {
      logWarn('WorldSecretStore refresh overview', e)
    } finally {
      loading.value = false
    }
  }

  function reset() {
    overview.value = null
    loaded.value = false
    loading.value = false
  }

  return {
    overview,
    loading,
    loaded,
    activeSecret,
    isNone,
    refreshOverview,
    reset,
  }
})
