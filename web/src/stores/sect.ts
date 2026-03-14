import { defineStore } from 'pinia'
import { computed, ref, shallowRef } from 'vue'
import type { SectTerritorySummaryDTO } from '../types/api'
import { worldApi } from '../api'
import { logWarn } from '../utils/appError'

export const useSectStore = defineStore('sect', () => {
  const territories = shallowRef<SectTerritorySummaryDTO[]>([])
  const isLoaded = ref(false)
  const isLoading = ref(false)

  let refreshRequestId = 0

  const activeTerritories = computed(() =>
    territories.value.filter(sect => sect.is_active !== false)
  )

  const activeSectOptions = computed(() =>
    activeTerritories.value.map(sect => ({
      label: sect.name,
      value: sect.id,
    }))
  )

  async function refreshTerritories() {
    const currentRequestId = ++refreshRequestId
    isLoading.value = true

    try {
      const response = await worldApi.fetchSectTerritories()
      if (currentRequestId !== refreshRequestId) return
      territories.value = response?.sects ?? []
      isLoaded.value = true
    } catch (error) {
      if (currentRequestId !== refreshRequestId) return
      logWarn('SectStore refresh territories', error)
      territories.value = []
      isLoaded.value = false
    } finally {
      if (currentRequestId === refreshRequestId) {
        isLoading.value = false
      }
    }
  }

  function reset() {
    territories.value = []
    isLoaded.value = false
    isLoading.value = false
  }

  return {
    territories,
    activeTerritories,
    activeSectOptions,
    isLoaded,
    isLoading,
    refreshTerritories,
    reset,
  }
})
