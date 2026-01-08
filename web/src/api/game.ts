import { httpClient } from './http';
import type { 
  InitialStateDTO, 
  MapResponseDTO, 
  DetailResponseDTO,
  SaveFileDTO
} from '../types/api';

export interface HoverParams {
  type: string;
  id: string;
}

// --- New Types ---

export interface GameDataDTO {
  sects: Array<{ id: number; name: string; alignment: string }>;
  personas: Array<{ id: number; name: string; desc: string; rarity: string }>;
  realms: string[];
  techniques: Array<{ id: number; name: string; grade: string; attribute: string; sect: string | null }>;
  weapons: Array<{ id: number; name: string; grade: string; type: string }>;
  auxiliaries: Array<{ id: number; name: string; grade: string }>;
  alignments: Array<{ value: string; label: string }>;
}

export interface SimpleAvatarDTO {
  id: string;
  name: string;
  sect_name: string;
  realm: string;
  gender: string;
  age: number;
}

export interface CreateAvatarParams {
  surname?: string;
  given_name?: string;
  gender?: string;
  age?: number;
  level?: number;
  sect_id?: number;
  persona_ids?: number[];
  pic_id?: number;
  technique_id?: number;
  weapon_id?: number;
  auxiliary_id?: number;
  alignment?: string;
  appearance?: number;
  relations?: Array<{ target_id: string; relation: string }>;
}

export interface PhenomenonDTO {
  id: number;
  name: string;
  desc: string;
  rarity: string;
  duration_years: number;
  effect_desc: string;
}

export interface LLMConfigDTO {
  base_url: string;
  api_key: string;
  model_name: string;
  fast_model_name: string;
  mode: string;
}

export interface InitStatusDTO {
  status: 'idle' | 'pending' | 'in_progress' | 'ready' | 'error';
  phase: number;
  phase_name: string;
  progress: number;
  elapsed_seconds: number;
  error: string | null;
  llm_check_failed: boolean;
  llm_error_message: string;
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

  fetchPhenomenaList() {
    return httpClient.get<{ phenomena: PhenomenonDTO[] }>('/api/meta/phenomena');
  },

  setPhenomenon(id: number) {
    return httpClient.post('/api/control/set_phenomenon', { id });
  },

  // --- Information ---

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
  },

  // --- Avatar Management ---
  
  fetchGameData() {
    return httpClient.get<GameDataDTO>('/api/meta/game_data');
  },

  fetchAvatarList() {
    return httpClient.get<{ avatars: SimpleAvatarDTO[] }>('/api/meta/avatar_list');
  },

  createAvatar(params: CreateAvatarParams) {
    return httpClient.post<{ status: string; message: string; avatar_id: string }>('/api/action/create_avatar', params);
  },

  deleteAvatar(avatarId: string) {
    return httpClient.post<{ status: string; message: string }>('/api/action/delete_avatar', { avatar_id: avatarId });
  },

  // --- LLM Config ---

  fetchLLMConfig() {
    return httpClient.get<LLMConfigDTO>('/api/config/llm');
  },

  testLLMConnection(config: LLMConfigDTO) {
    return httpClient.post<{ status: string; message: string }>('/api/config/llm/test', config);
  },

  saveLLMConfig(config: LLMConfigDTO) {
    return httpClient.post<{ status: string; message: string }>('/api/config/llm/save', config);
  },

  // --- Init Status ---

  fetchInitStatus() {
    return httpClient.get<InitStatusDTO>('/api/init-status');
  },

  startNewGame() {
    return httpClient.post<{ status: string; message: string }>('/api/game/new', {});
  },

  reinitGame() {
    return httpClient.post<{ status: string; message: string }>('/api/control/reinit', {});
  }
};
