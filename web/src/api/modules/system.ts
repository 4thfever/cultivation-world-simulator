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
    return httpClient.post('/api/control/pause', {});
  },

  resumeGame() {
    return httpClient.post('/api/control/resume', {});
  },

  fetchSaves() {
    return httpClient.get<{ saves: SaveFileDTO[] }>('/api/saves');
  },

  saveGame(customName?: string) {
    return httpClient.post<{ status: string; filename: string }>(
      '/api/game/save',
      { custom_name: customName }
    );
  },

  deleteSave(filename: string) {
    return httpClient.post<{ status: string; message: string }>('/api/game/delete', { filename });
  },

  loadGame(filename: string) {
    return httpClient.post<{ status: string; message: string }>('/api/game/load', { filename });
  },

  fetchInitStatus() {
    return httpClient.get<InitStatusDTO>('/api/init-status');
  },

  startNewGame() {
    return httpClient.post<{ status: string; message: string }>('/api/game/new', {});
  },

  reinitGame() {
    return httpClient.post<{ status: string; message: string }>('/api/control/reinit', {});
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
    return httpClient.post<{ status: string; message: string }>('/api/game/start', config);
  },

  fetchCurrentRun() {
    return httpClient.get<RunConfigDTO>('/api/game/current-run');
  },

  shutdown() {
    return httpClient.post<{ status: string; message: string }>('/api/control/shutdown', {});
  },

  resetGame() {
    return httpClient.post<{ status: string; message: string }>('/api/control/reset', {});
  }
};
