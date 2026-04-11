import type {
  InitialStateDTO,
  MapRenderConfigDTO,
  MapResponseDTO,
  PhenomenonDTO,
  RankingsDTO,
  RankingAvatarDTO,
  RankingSectDTO,
  TournamentSummaryDTO,
} from '@/types/api'
import type { AvatarSummary, CelestialPhenomenon, RegionSummary } from '@/types/core'

export interface WorldStateSnapshot {
  status: InitialStateDTO['status']
  year: number
  month: number
  avatars: AvatarSummary[]
  events: NonNullable<InitialStateDTO['events']>
  phenomenon: CelestialPhenomenon | null
  activeDomains: NonNullable<InitialStateDTO['active_domains']>
}

export interface WorldMapSnapshot {
  data: MapResponseDTO['data']
  regions: RegionSummary[]
  renderConfig: MapRenderConfigDTO
}

export function normalizeMapRenderConfig(config?: MapRenderConfigDTO): MapRenderConfigDTO {
  return {
    water_speed: config?.water_speed ?? 'high',
    cloud_frequency: config?.cloud_frequency ?? 'none',
  }
}

export function normalizeInitialState(input: InitialStateDTO): WorldStateSnapshot {
  return {
    status: input.status,
    year: input.year,
    month: input.month,
    avatars: Array.isArray(input.avatars)
      ? input.avatars.map((avatar) => ({
          ...avatar,
          name: avatar.name ?? '',
        }))
      : [],
    events: Array.isArray(input.events) ? input.events : [],
    phenomenon: input.phenomenon ?? null,
    activeDomains: Array.isArray(input.active_domains) ? input.active_domains : [],
  }
}

export function normalizeMapResponse(input: MapResponseDTO): WorldMapSnapshot {
  return {
    data: Array.isArray(input.data) ? input.data : [],
    regions: Array.isArray(input.regions)
      ? input.regions.map((region) => ({
          ...region,
          id: String(region.id),
        }))
      : [],
    renderConfig: normalizeMapRenderConfig(input.render_config),
  }
}

export function normalizePhenomenaList(
  input: { phenomena?: PhenomenonDTO[] } | null | undefined,
): CelestialPhenomenon[] {
  return Array.isArray(input?.phenomena) ? input.phenomena : []
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

