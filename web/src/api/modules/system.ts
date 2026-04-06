import { httpClient } from '../http';
import type { 
  SaveFileDTO,
  InitStatusDTO,
  RunConfigDTO,
  AppSettingsDTO,
  AppSettingsPatchDTO
} from '../../types/api';

export const systemApi = {
  pauseGame() {
    return httpClient.post('/api/v1/command/game/pause', {});
  },

  resumeGame() {
    return httpClient.post('/api/v1/command/game/resume', {});
  },

  fetchSaves() {
    return httpClient.get<{ saves: SaveFileDTO[] }>('/api/v1/query/saves')
      .then((data) => data.saves ?? []);
  },

  saveGame(customName?: string) {
    return httpClient.post<{ status: string; filename: string }>(
      '/api/v1/command/game/save',
      { custom_name: customName }
    );
  },

  deleteSave(filename: string) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/game/delete-save', { filename });
  },

  loadGame(filename: string) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/game/load', { filename });
  },

  fetchInitStatus() {
    return httpClient.get<InitStatusDTO>('/api/v1/query/runtime/status');
  },

  startNewGame() {
    return this.reinitGame();
  },

  reinitGame() {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/game/reinit', {});
  },

  fetchSettings() {
    return httpClient.get<AppSettingsDTO>('/api/settings');
  },

  patchSettings(patch: AppSettingsPatchDTO) {
    return httpClient.patch<AppSettingsDTO>('/api/settings', patch);
  },

  resetSettings() {
    return httpClient.post<AppSettingsDTO>('/api/settings/reset', {});
  },

  startGame(config: RunConfigDTO) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/game/start', config);
  },

  fetchCurrentRun() {
    return httpClient.get<RunConfigDTO>('/api/v1/query/system/current-run');
  },

  shutdown() {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/system/shutdown', {});
  },

  resetGame() {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/game/reset', {});
  }
};
