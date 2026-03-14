import { httpClient } from '../http';
import type { 
  InitialStateDTO, 
  MapResponseDTO, 
  PhenomenonDTO,
  RankingsDTO,
  SectRelationsResponseDTO,
  SectTerritoriesResponseDTO,
} from '../../types/api';
import { normalizeRankingsResponse } from '../mappers/world';

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
};
