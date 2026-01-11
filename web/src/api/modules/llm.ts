import { httpClient } from '../http';
import type { LLMConfigDTO } from '../../types/api';

export const llmApi = {
  fetchConfig() {
    return httpClient.get<LLMConfigDTO>('/api/config/llm');
  },

  testConnection(config: LLMConfigDTO) {
    return httpClient.post<{ status: string; message: string }>('/api/config/llm/test', config);
  },

  saveConfig(config: LLMConfigDTO) {
    return httpClient.post<{ status: string; message: string }>('/api/config/llm/save', config);
  },
  
  fetchStatus() {
    return httpClient.get<{ configured: boolean }>('/api/config/llm/status');
  }
};
