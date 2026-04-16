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
  RoleplaySessionDTO,
} from '../../types/api';

export interface HoverParams {
  type: string;
  id: string;
}

export const avatarApi = {
  fetchAvatarMeta() {
    return httpClient.get<{ males: number[]; females: number[] }>('/api/v1/query/meta/avatars');
  },

  fetchDetailInfo(params: HoverParams) {
    const query = new URLSearchParams(Object.entries(params));
    return httpClient.get<DetailResponseDTO>(`/api/v1/query/detail?${query}`);
  },

  setLongTermObjective(avatarId: string, content: string) {
    return httpClient.post('/api/v1/command/avatar/set-long-term-objective', {
      avatar_id: avatarId,
      content
    });
  },

  clearLongTermObjective(avatarId: string) {
    return httpClient.post('/api/v1/command/avatar/clear-long-term-objective', {
      avatar_id: avatarId
    });
  },

  fetchGameData() {
    return httpClient.get<GameDataDTO>('/api/v1/query/meta/game-data');
  },

  fetchAvatarList() {
    return httpClient.get<{ avatars: SimpleAvatarDTO[] }>('/api/v1/query/meta/avatar-list')
      .then((data) => data.avatars ?? []);
  },

  fetchAvatarAdjustOptions() {
    return httpClient.get<AvatarAdjustCatalogDTO>('/api/v1/query/meta/avatar-adjust-options');
  },

  createAvatar(params: CreateAvatarParams) {
    return httpClient.post<{ status: string; message: string; avatar_id: string }>('/api/v1/command/avatar/create', params);
  },

  updateAvatarAdjustment(params: UpdateAvatarAdjustmentParams) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/avatar/update-adjustment', params);
  },

  updateAvatarPortrait(params: UpdateAvatarPortraitParams) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/avatar/update-portrait', params);
  },

  generateCustomContent(params: GenerateCustomContentParams) {
    return httpClient.post<{ status: string; draft: CustomContentDraftDTO }>('/api/v1/command/avatar/generate-custom-content', params);
  },

  createCustomContent(params: CreateCustomContentParams) {
    return httpClient.post<{ status: string; item: AvatarAdjustOptionDTO }>('/api/v1/command/avatar/create-custom-content', params);
  },

  deleteAvatar(avatarId: string) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/avatar/delete', { avatar_id: avatarId });
  },

  fetchRoleplaySession() {
    return httpClient.get<RoleplaySessionDTO>('/api/v1/query/roleplay/session');
  },

  startRoleplay(avatarId: string) {
    return httpClient.post<RoleplaySessionDTO>('/api/v1/command/roleplay/start', {
      avatar_id: avatarId,
    });
  },

  stopRoleplay(avatarId?: string) {
    return httpClient.post<RoleplaySessionDTO>('/api/v1/command/roleplay/stop', {
      avatar_id: avatarId,
    });
  },

  submitRoleplayDecision(params: { avatar_id: string; request_id: string; command_text: string }) {
    return httpClient.post<{ status: string; message: string; planned_action_count: number }>(
      '/api/v1/command/roleplay/submit-decision',
      params,
    );
  },

  submitRoleplayChoice(params: { avatar_id: string; request_id: string; selected_key: string }) {
    return httpClient.post<{ status: string; message: string; result?: unknown }>(
      '/api/v1/command/roleplay/submit-choice',
      params,
    );
  }
};
