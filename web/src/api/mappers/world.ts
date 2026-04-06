import type { MapRenderConfigDTO, RankingsDTO, RankingAvatarDTO, RankingSectDTO, TournamentSummaryDTO } from '@/types/api'

export function normalizeMapRenderConfig(config?: MapRenderConfigDTO): MapRenderConfigDTO {
  return {
    water_speed: config?.water_speed ?? 'high',
    cloud_frequency: config?.cloud_frequency ?? 'none',
  }
}

function normalizeAvatarRankList(list: RankingAvatarDTO[] | undefined): RankingAvatarDTO[] {
  return Array.isArray(list) ? list : []
}

function normalizeSectRankList(list: RankingSectDTO[] | undefined): RankingSectDTO[] {
  return Array.isArray(list) ? list : []
}

function normalizeTournament(tournament?: TournamentSummaryDTO): TournamentSummaryDTO | undefined {
  if (!tournament) return undefined
  return {
    next_year: tournament.next_year ?? 0,
    heaven_first: tournament.heaven_first,
    earth_first: tournament.earth_first,
    human_first: tournament.human_first,
  }
}

export function normalizeRankingsResponse(input: Partial<RankingsDTO> | null | undefined): RankingsDTO {
  return {
    heaven: normalizeAvatarRankList(input?.heaven),
    earth: normalizeAvatarRankList(input?.earth),
    human: normalizeAvatarRankList(input?.human),
    sect: normalizeSectRankList(input?.sect),
    tournament: normalizeTournament(input?.tournament),
  }
}

