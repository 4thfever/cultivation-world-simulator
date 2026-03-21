import { defineStore } from 'pinia'
import { ref, shallowRef } from 'vue'
import { worldApi } from '@/api'
import type { MortalOverview } from '@/types/core'
import { logWarn } from '@/utils/appError'

function createEmptyOverview(): MortalOverview {
  return {
    summary: {
      total_population: 0,
      total_population_capacity: 0,
      total_natural_growth: 0,
      tracked_mortal_count: 0,
      awakening_candidate_count: 0,
    },
    cities: [],
    tracked_mortals: [],
  }
}

export const useMortalStore = defineStore('mortal', () => {
  const overview = shallowRef<MortalOverview>(createEmptyOverview())
  const isLoading = ref(false)
  const isLoaded = ref(false)

  let refreshRequestId = 0

  async function refreshOverview() {
    const currentRequestId = ++refreshRequestId
    isLoading.value = true

    try {
      const data = await worldApi.fetchMortalOverview()
      if (currentRequestId !== refreshRequestId) return
      overview.value = data
      isLoaded.value = true
    } catch (error) {
      if (currentRequestId !== refreshRequestId) return
      logWarn('MortalStore refresh overview', error)
      overview.value = createEmptyOverview()
      isLoaded.value = false
    } finally {
      if (currentRequestId === refreshRequestId) {
        isLoading.value = false
      }
    }
  }

  function reset() {
    overview.value = createEmptyOverview()
    isLoading.value = false
    isLoaded.value = false
  }

  return {
    overview,
    isLoading,
    isLoaded,
    refreshOverview,
    reset,
  }
})
