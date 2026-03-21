import type { DynastyOverviewResponseDTO } from '@/types/api'
import type { DynastyOverview } from '@/types/core'

export function normalizeDynastyOverview(input: DynastyOverviewResponseDTO | null | undefined): DynastyOverview {
  return {
    name: String(input?.name ?? ''),
    title: String(input?.title ?? ''),
    royal_surname: String(input?.royal_surname ?? ''),
    royal_house_name: String(input?.royal_house_name ?? ''),
    desc: String(input?.desc ?? ''),
    effect_desc: String(input?.effect_desc ?? ''),
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
