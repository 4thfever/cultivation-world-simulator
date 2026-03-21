import { defineStore } from 'pinia'
import { ref, shallowRef } from 'vue'
import { worldApi } from '@/api'
import type { DynastyOverview } from '@/types/core'
import { logWarn } from '@/utils/appError'

function createEmptyOverview(): DynastyOverview {
  return {
    name: '',
    title: '',
    royal_surname: '',
    royal_house_name: '',
    desc: '',
    effect_desc: '',
    is_low_magic: true,
    current_emperor: null,
  }
}

export const useDynastyStore = defineStore('dynasty', () => {
  const overview = shallowRef<DynastyOverview>(createEmptyOverview())
  const isLoading = ref(false)
  const isLoaded = ref(false)

  let refreshRequestId = 0

  async function refreshOverview() {
    const currentRequestId = ++refreshRequestId
    isLoading.value = true

    try {
      const data = await worldApi.fetchDynastyOverview()
      if (currentRequestId !== refreshRequestId) return
      overview.value = data
      isLoaded.value = true
    } catch (error) {
      if (currentRequestId !== refreshRequestId) return
      logWarn('DynastyStore refresh overview', error)
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
