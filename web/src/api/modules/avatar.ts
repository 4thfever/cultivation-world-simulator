import { httpClient } from '../http';
import type { 
  DetailResponseDTO,
  SimpleAvatarDTO,
  CreateAvatarParams,
  GameDataDTO,
  AvatarAdjustCatalogDTO,
  AvatarAdjustOptionDTO,
  UpdateAvatarAdjustmentParams,
  UpdateAvatarPortraitParams,
  GenerateCustomContentParams,
  CustomContentDraftDTO,
  CreateCustomContentParams,
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

  fetchAvatarAdjustOptions() {
    return httpClient.get<AvatarAdjustCatalogDTO>('/api/meta/avatar_adjust_options');
  },

  createAvatar(params: CreateAvatarParams) {
    return httpClient.post<{ status: string; message: string; avatar_id: string }>('/api/action/create_avatar', params);
  },

  updateAvatarAdjustment(params: UpdateAvatarAdjustmentParams) {
    return httpClient.post<{ status: string; message: string }>('/api/action/update_avatar_adjustment', params);
  },

  updateAvatarPortrait(params: UpdateAvatarPortraitParams) {
    return httpClient.post<{ status: string; message: string }>('/api/action/update_avatar_portrait', params);
  },

  generateCustomContent(params: GenerateCustomContentParams) {
    return httpClient.post<{ status: string; draft: CustomContentDraftDTO }>('/api/action/generate_custom_content', params);
  },

  createCustomContent(params: CreateCustomContentParams) {
    return httpClient.post<{ status: string; item: AvatarAdjustOptionDTO }>('/api/action/create_custom_content', params);
  },

  deleteAvatar(avatarId: string) {
    return httpClient.post<{ status: string; message: string }>('/api/action/delete_avatar', { avatar_id: avatarId });
  }
};
