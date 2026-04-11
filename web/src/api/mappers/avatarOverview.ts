import type { AvatarOverviewResponseDTO } from '@/types/api'
import type { AvatarOverview } from '@/types/core'

export function normalizeAvatarOverview(input: AvatarOverviewResponseDTO): AvatarOverview {
  return {
    summary: {
      totalCount: input.summary?.total_count ?? 0,
      aliveCount: input.summary?.alive_count ?? 0,
      deadCount: input.summary?.dead_count ?? 0,
      sectMemberCount: input.summary?.sect_member_count ?? 0,
      rogueCount: input.summary?.rogue_count ?? 0,
    },
    realmDistribution: Array.isArray(input.realm_distribution)
      ? input.realm_distribution.map((item) => ({
          realm: item.realm ?? '',
          count: item.count ?? 0,
        }))
      : [],
  }
}
