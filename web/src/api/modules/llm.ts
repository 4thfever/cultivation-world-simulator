import { httpClient } from '../http';
import type { LLMConfigDTO, LLMConfigViewDTO } from '../../types/api';

export const llmApi = {
  fetchConfig() {
    return httpClient.get<LLMConfigViewDTO>('/api/settings/llm');
  },

  testConnection(config: LLMConfigDTO) {
    return httpClient.post<{ status: string; message: string }>('/api/settings/llm/test', config);
  },

  saveConfig(config: LLMConfigDTO) {
    return httpClient.put<{ status: string; message: string; config: LLMConfigViewDTO }>('/api/settings/llm', config);
  },
  
  fetchStatus() {
    return httpClient.get<{ configured: boolean }>('/api/settings/llm/status');
  }
};
