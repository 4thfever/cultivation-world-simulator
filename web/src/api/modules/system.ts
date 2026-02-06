import { httpClient } from '../http';
import type { 
  SaveFileDTO,
  InitStatusDTO,
  GameStartConfigDTO,
  CurrentConfigDTO
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

  fetchCurrentConfig() {
    return httpClient.get<CurrentConfigDTO>('/api/config/current');
  },

  startGame(config: GameStartConfigDTO) {
    return httpClient.post<{ status: string; message: string }>('/api/game/start', config);
  },

  shutdown() {
    return httpClient.post<{ status: string; message: string }>('/api/control/shutdown', {});
  },

  setLanguage(lang: string) {
    return httpClient.post<{ status: string }>('/api/config/language', { lang });
  },

  fetchLanguage() {
    return httpClient.get<{ lang: string }>('/api/config/language');
  },

  resetGame() {
    return httpClient.post<{ status: string; message: string }>('/api/control/reset', {});
  }
};
