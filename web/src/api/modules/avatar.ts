import { httpClient } from '../http';
import type { 
  DetailResponseDTO,
  SimpleAvatarDTO,
  CreateAvatarParams,
  GameDataDTO
} from '../../types/api';

export interface HoverParams {
  type: string;
  id: string;
}

export const avatarApi = {
  fetchAvatarMeta() {
    // Add timestamp to prevent caching
    return httpClient.get<{ males: number[]; females: number[] }>(`/api/meta/avatars?t=${Date.now()}`);
  },

  fetchDetailInfo(params: HoverParams) {
    const query = new URLSearchParams(Object.entries(params));
    return httpClient.get<DetailResponseDTO>(`/api/detail?${query}`);
  },

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
  }
};
