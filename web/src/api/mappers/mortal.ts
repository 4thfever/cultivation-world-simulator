import type {
  MortalOverviewResponseDTO,
  MortalCityOverviewDTO,
  TrackedMortalDTO,
} from '@/types/api'
import type {
  MortalOverview,
  MortalCityOverview,
  TrackedMortalInfo,
} from '@/types/core'

function normalizeCity(item: MortalCityOverviewDTO): MortalCityOverview {
  return {
    id: Number(item.id ?? 0),
    name: String(item.name ?? ''),
    population: Number(item.population ?? 0),
    population_capacity: Number(item.population_capacity ?? 0),
    natural_growth: Number(item.natural_growth ?? 0),
  }
}

function normalizeTrackedMortal(item: TrackedMortalDTO): TrackedMortalInfo {
  return {
    id: String(item.id ?? ''),
    name: String(item.name ?? ''),
    gender: String(item.gender ?? ''),
    age: Number(item.age ?? 0),
    born_region_id: Number(item.born_region_id ?? -1),
    born_region_name: String(item.born_region_name ?? ''),
    parents: Array.isArray(item.parents) ? item.parents.map(parent => String(parent)) : [],
    is_awakening_candidate: Boolean(item.is_awakening_candidate),
  }
}

export function normalizeMortalOverview(input: MortalOverviewResponseDTO | null | undefined): MortalOverview {
  return {
    summary: {
      total_population: Number(input?.summary?.total_population ?? 0),
      total_population_capacity: Number(input?.summary?.total_population_capacity ?? 0),
      total_natural_growth: Number(input?.summary?.total_natural_growth ?? 0),
      tracked_mortal_count: Number(input?.summary?.tracked_mortal_count ?? 0),
      awakening_candidate_count: Number(input?.summary?.awakening_candidate_count ?? 0),
    },
    cities: Array.isArray(input?.cities) ? input!.cities.map(normalizeCity) : [],
    tracked_mortals: Array.isArray(input?.tracked_mortals)
      ? input!.tracked_mortals.map(normalizeTrackedMortal)
      : [],
  }
}
