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
import { normalizeRankingsResponse } from '../mappers/world';
import { normalizeMortalOverview } from '../mappers/mortal';
import { normalizeDynastyDetail, normalizeDynastyOverview } from '../mappers/dynasty';

export const worldApi = {
  fetchInitialState() {
    return httpClient.get<InitialStateDTO>('/api/state');
  },

  fetchMap() {
    return httpClient.get<MapResponseDTO>('/api/map');
  },

  fetchPhenomenaList() {
    return httpClient.get<{ phenomena: PhenomenonDTO[] }>('/api/meta/phenomena');
  },

  setPhenomenon(id: number) {
    return httpClient.post('/api/control/set_phenomenon', { id });
  },

  async fetchRankings() {
    const data = await httpClient.get<Partial<RankingsDTO>>('/api/rankings');
    return normalizeRankingsResponse(data);
  },

  fetchSectRelations() {
    return httpClient.get<SectRelationsResponseDTO>('/api/sect-relations');
  },

  fetchSectTerritories() {
    return httpClient.get<SectTerritoriesResponseDTO>('/api/sects/territories');
  },

  async fetchMortalOverview() {
    const data = await httpClient.get<MortalOverviewResponseDTO>('/api/mortals/overview');
    return normalizeMortalOverview(data);
  },

  async fetchDynastyOverview() {
    const data = await httpClient.get<DynastyOverviewResponseDTO>('/api/dynasty/overview');
    return normalizeDynastyOverview(data);
  },

  async fetchDynastyDetail() {
    const data = await httpClient.get<DynastyDetailResponseDTO>('/api/dynasty/detail');
    return normalizeDynastyDetail(data);
  },
};
