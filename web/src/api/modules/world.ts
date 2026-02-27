import { httpClient } from '../http';
import type { 
  InitialStateDTO, 
  MapResponseDTO, 
  PhenomenonDTO
} from '../../types/api';

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

  fetchRankings() {
    return httpClient.get<any>('/api/rankings');
  }
};
