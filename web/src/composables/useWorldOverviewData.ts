import { computed, ref } from 'vue'
import { worldApi } from '@/api/modules/world'
import type { RankingsDTO, SectRelationDTO } from '@/types/api'
import { logError } from '@/utils/appError'

export const createEmptyRankings = (): RankingsDTO => ({
  heaven: [],
  earth: [],
  human: [],
  sect: [],
})

export function useWorldOverviewData(logScope: string) {
  const rankingsLoading = ref(false)
  const relationsLoading = ref(false)
  const loading = computed(() => rankingsLoading.value || relationsLoading.value)
  const rankings = ref<RankingsDTO>(createEmptyRankings())
  const relations = ref<SectRelationDTO[]>([])

  const fetchRankings = async () => {
    rankingsLoading.value = true
    try {
      rankings.value = await worldApi.fetchRankings()
    } catch (error) {
      rankings.value = createEmptyRankings()
      logError(`${logScope} fetch rankings`, error)
    } finally {
      rankingsLoading.value = false
    }
  }

  const fetchRelations = async () => {
    relationsLoading.value = true
    try {
      const result = await worldApi.fetchSectRelations()
      relations.value = result.relations ?? []
    } catch (error) {
      relations.value = []
      logError(`${logScope} fetch sect relations`, error)
    } finally {
      relationsLoading.value = false
    }
  }

  const fetchRankingsAndRelations = async () => {
    rankingsLoading.value = true
    relationsLoading.value = true
    try {
      const [rankingsResult, relationsResult] = await Promise.allSettled([
        worldApi.fetchRankings(),
        worldApi.fetchSectRelations(),
      ])

      if (rankingsResult.status === 'fulfilled') {
        rankings.value = rankingsResult.value
      } else {
        rankings.value = createEmptyRankings()
        logError(`${logScope} fetch rankings`, rankingsResult.reason)
      }

      if (relationsResult.status === 'fulfilled') {
        relations.value = relationsResult.value.relations ?? []
      } else {
        relations.value = []
        logError(`${logScope} fetch sect relations`, relationsResult.reason)
      }
    } finally {
      rankingsLoading.value = false
      relationsLoading.value = false
    }
  }

  return {
    loading,
    rankingsLoading,
    relationsLoading,
    rankings,
    relations,
    fetchRankings,
    fetchRelations,
    fetchRankingsAndRelations,
  }
}
