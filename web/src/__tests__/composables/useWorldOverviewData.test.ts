import { describe, expect, it, vi } from 'vitest'
import { useWorldOverviewData } from '@/composables/useWorldOverviewData'
import { worldApi } from '@/api/modules/world'

vi.mock('@/api/modules/world', () => ({
  worldApi: {
    fetchRankings: vi.fn(),
    fetchSectRelations: vi.fn(),
  },
}))

describe('useWorldOverviewData', () => {
  it('keeps combined loading true until concurrent requests both settle', async () => {
    let resolveRankings: (value: unknown) => void = () => {}
    let resolveRelations: (value: unknown) => void = () => {}
    vi.mocked(worldApi.fetchRankings).mockReturnValue(new Promise(resolve => {
      resolveRankings = resolve
    }) as never)
    vi.mocked(worldApi.fetchSectRelations).mockReturnValue(new Promise(resolve => {
      resolveRelations = resolve
    }) as never)

    const data = useWorldOverviewData('test')
    const rankingsPromise = data.fetchRankings()
    const relationsPromise = data.fetchRelations()

    expect(data.loading.value).toBe(true)
    expect(data.rankingsLoading.value).toBe(true)
    expect(data.relationsLoading.value).toBe(true)

    resolveRankings({ heaven: [], earth: [], human: [], sect: [] })
    await rankingsPromise

    expect(data.rankingsLoading.value).toBe(false)
    expect(data.relationsLoading.value).toBe(true)
    expect(data.loading.value).toBe(true)

    resolveRelations({ relations: [] })
    await relationsPromise

    expect(data.relationsLoading.value).toBe(false)
    expect(data.loading.value).toBe(false)
  })
})
