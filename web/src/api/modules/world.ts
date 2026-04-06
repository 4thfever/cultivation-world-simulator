import { httpClient } from '../http';
import type { 
  InitialStateDTO, 
  MapResponseDTO, 
  PhenomenonDTO,
  RankingsDTO,
  SectRelationsResponseDTO,
  SectTerritoriesResponseDTO,
  MortalOverviewResponseDTO,
  DynastyDetailResponseDTO,
  DynastyOverviewResponseDTO,
} from '../../types/api';
import {
  normalizeInitialState,
  normalizeMapResponse,
  normalizePhenomenaList,
  normalizeRankingsResponse,
} from '../mappers/world';
import { normalizeMortalOverview } from '../mappers/mortal';
import { normalizeDynastyDetail, normalizeDynastyOverview } from '../mappers/dynasty';

export const worldApi = {
  async fetchInitialState() {
    const data = await httpClient.get<InitialStateDTO>('/api/v1/query/world/state');
    return normalizeInitialState(data);
  },

  async fetchMap() {
    const data = await httpClient.get<MapResponseDTO>('/api/v1/query/world/map');
    return normalizeMapResponse(data);
  },

  async fetchPhenomenaList() {
    const data = await httpClient.get<{ phenomena: PhenomenonDTO[] }>('/api/v1/query/meta/phenomena');
    return normalizePhenomenaList(data);
  },

  setPhenomenon(id: number) {
    return httpClient.post('/api/v1/command/world/set-phenomenon', { id });
  },

  async fetchRankings() {
    const data = await httpClient.get<Partial<RankingsDTO>>('/api/v1/query/rankings');
    return normalizeRankingsResponse(data);
  },

  fetchSectRelations() {
    return httpClient.get<SectRelationsResponseDTO>('/api/v1/query/sect-relations');
  },

  fetchSectTerritories() {
    return httpClient.get<SectTerritoriesResponseDTO>('/api/v1/query/sects/territories');
  },

  async fetchMortalOverview() {
    const data = await httpClient.get<MortalOverviewResponseDTO>('/api/v1/query/mortals/overview');
    return normalizeMortalOverview(data);
  },

  async fetchDynastyOverview() {
    const data = await httpClient.get<DynastyOverviewResponseDTO>('/api/v1/query/dynasty/overview');
    return normalizeDynastyOverview(data);
  },

  async fetchDynastyDetail() {
    const data = await httpClient.get<DynastyDetailResponseDTO>('/api/v1/query/dynasty/detail');
    return normalizeDynastyDetail(data);
  },
};
