import { defineStore } from 'pinia'
import { ref, shallowRef } from 'vue'
import { worldApi } from '@/api'
import type { AvatarOverview } from '@/types/core'
import { logWarn } from '@/utils/appError'

function createEmptyOverview(): AvatarOverview {
  return {
    summary: {
      totalCount: 0,
      aliveCount: 0,
      deadCount: 0,
      sectMemberCount: 0,
      rogueCount: 0,
    },
    realmDistribution: [],
  }
}

export const useAvatarOverviewStore = defineStore('avatarOverview', () => {
  const overview = shallowRef<AvatarOverview>(createEmptyOverview())
  const isLoading = ref(false)
  const isLoaded = ref(false)

  let refreshRequestId = 0

  async function refreshOverview() {
    const currentRequestId = ++refreshRequestId
    isLoading.value = true

    try {
      const data = await worldApi.fetchAvatarOverview()
      if (currentRequestId !== refreshRequestId) return
      overview.value = data
      isLoaded.value = true
    } catch (error) {
      if (currentRequestId !== refreshRequestId) return
      logWarn('AvatarOverviewStore refresh overview', error)
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
