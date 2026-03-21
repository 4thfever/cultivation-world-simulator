import type { DynastyDetailResponseDTO, DynastyOverviewResponseDTO } from '@/types/api'
import type { DynastyDetail, DynastyOverview } from '@/types/core'

export function normalizeDynastyOverview(input: DynastyOverviewResponseDTO | null | undefined): DynastyOverview {
  return {
    name: String(input?.name ?? ''),
    title: String(input?.title ?? ''),
    royal_surname: String(input?.royal_surname ?? ''),
    royal_house_name: String(input?.royal_house_name ?? ''),
    desc: String(input?.desc ?? ''),
    effect_desc: String(input?.effect_desc ?? ''),
    style_tag: String(input?.style_tag ?? ''),
    official_preference_label: String(input?.official_preference_label ?? ''),
    is_low_magic: Boolean(input?.is_low_magic ?? true),
    current_emperor: input?.current_emperor
      ? {
          name: String(input.current_emperor.name ?? ''),
          surname: String(input.current_emperor.surname ?? ''),
          given_name: String(input.current_emperor.given_name ?? ''),
          age: Number(input.current_emperor.age ?? 0),
          max_age: Number(input.current_emperor.max_age ?? 80),
          is_mortal: Boolean(input.current_emperor.is_mortal ?? true),
        }
      : null,
  }
}

export function normalizeDynastyDetail(input: DynastyDetailResponseDTO | null | undefined): DynastyDetail {
  return {
    overview: normalizeDynastyOverview(input?.overview),
    summary: {
      officialCount: Number(input?.summary?.official_count ?? 0),
      topOfficialRankName: String(input?.summary?.top_official_rank_name ?? ''),
    },
    officials: (input?.officials ?? []).map((item) => ({
      id: String(item?.id ?? ''),
      name: String(item?.name ?? ''),
      realm: String(item?.realm ?? ''),
      officialRankKey: String(item?.official_rank_key ?? ''),
      officialRankName: String(item?.official_rank_name ?? ''),
      courtReputation: Number(item?.court_reputation ?? 0),
      sectName: String(item?.sect_name ?? ''),
    })),
  }
}
