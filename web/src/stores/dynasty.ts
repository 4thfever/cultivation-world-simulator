import { defineStore } from 'pinia'
import { computed, ref, shallowRef } from 'vue'
import { worldApi } from '@/api'
import type { DynastyDetail, DynastyOverview } from '@/types/core'
import { logWarn } from '@/utils/appError'

function createEmptyOverview(): DynastyOverview {
  return {
    name: '',
    title: '',
    royal_surname: '',
    royal_house_name: '',
    desc: '',
    effect_desc: '',
    style_tag: '',
    official_preference_label: '',
    is_low_magic: true,
    current_emperor: null,
  }
}

function createEmptyDetail(): DynastyDetail {
  return {
    overview: createEmptyOverview(),
    summary: {
      officialCount: 0,
      topOfficialRankName: '',
    },
    officials: [],
  }
}

export const useDynastyStore = defineStore('dynasty', () => {
  const detail = shallowRef<DynastyDetail>(createEmptyDetail())
  const isLoading = ref(false)
  const isLoaded = ref(false)

  let refreshRequestId = 0

  const overview = computed(() => detail.value.overview)
  const officials = computed(() => detail.value.officials)
  const summary = computed(() => detail.value.summary)

  async function refreshDetail() {
    const currentRequestId = ++refreshRequestId
    isLoading.value = true

    try {
      const data = await worldApi.fetchDynastyDetail()
      if (currentRequestId !== refreshRequestId) return
      detail.value = data
      isLoaded.value = true
    } catch (error) {
      if (currentRequestId !== refreshRequestId) return
      logWarn('DynastyStore refresh detail', error)
      detail.value = createEmptyDetail()
      isLoaded.value = false
    } finally {
      if (currentRequestId === refreshRequestId) {
        isLoading.value = false
      }
    }
  }

  async function refreshOverview() {
    await refreshDetail()
  }

  function reset() {
    detail.value = createEmptyDetail()
    isLoading.value = false
    isLoaded.value = false
  }

  return {
    detail,
    overview,
    officials,
    summary,
    isLoading,
    isLoaded,
    refreshDetail,
    refreshOverview,
    reset,
  }
})
