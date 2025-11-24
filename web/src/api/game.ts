import { httpClient } from './http';
import type { 
  InitialStateDTO, 
  MapResponseDTO, 
  HoverResponseDTO, 
  DetailResponseDTO,
  SaveFileDTO
} from '../types/api';

export interface HoverParams {
  type: string;
  id: string;
}

export const gameApi = {
  // --- World State ---
  
  fetchInitialState() {
    return httpClient.get<InitialStateDTO>('/api/state');
  },

  fetchMap() {
    return httpClient.get<MapResponseDTO>('/api/map');
  },

  fetchAvatarMeta() {
    return httpClient.get<{ males: number[]; females: number[] }>('/api/meta/avatars');
  },

  // --- Information ---

  fetchHoverInfo(params: HoverParams) {
    const query = new URLSearchParams(Object.entries(params));
    return httpClient.get<HoverResponseDTO>(`/api/hover?${query}`);
  },

  fetchDetailInfo(params: HoverParams) {
    const query = new URLSearchParams(Object.entries(params));
    return httpClient.get<DetailResponseDTO>(`/api/detail?${query}`);
  },

  // --- Actions ---

  setLongTermObjective(avatarId: string, content: string) {
    return httpClient.post('/api/action/set_long_term_objective', {
      avatar_id: avatarId,
      content
    });
  },

  clearLongTermObjective(avatarId: string) {
    return httpClient.post('/api/action/clear_long_term_objective', {
      avatar_id: avatarId
    });
  },

  // --- Controls ---

  pauseGame() {
    return httpClient.post('/api/control/pause', {});
  },

  resumeGame() {
    return httpClient.post('/api/control/resume', {});
  },

  // --- Saves ---

  fetchSaves() {
    return httpClient.get<{ saves: SaveFileDTO[] }>('/api/saves');
  },

  saveGame(filename?: string) {
    return httpClient.post<{ status: string; filename: string }>('/api/game/save', { filename });
  },

  loadGame(filename: string) {
    return httpClient.post<{ status: string; message: string }>('/api/game/load', { filename });
  }
};

