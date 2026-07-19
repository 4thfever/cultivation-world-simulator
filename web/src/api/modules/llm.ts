import { httpClient } from '../http';
import type { LLMConfigDTO, LLMConfigViewDTO, LLMStatusDTO } from '../../types/api';

const LLM_TEST_TIMEOUT_MS = 150000;

export const llmApi = {
  fetchConfig() {
    return httpClient.get<LLMConfigViewDTO>('/api/settings/llm');
  },

  testConnection(config: LLMConfigDTO) {
    return httpClient.post<{ status: string; message: string }>(
      '/api/settings/llm/test',
      config,
      { timeoutMs: LLM_TEST_TIMEOUT_MS },
    );
  },

  saveConfig(config: LLMConfigDTO) {
    return httpClient.put<{ status: string; message: string; config: LLMConfigViewDTO }>('/api/settings/llm', config);
  },
  
  fetchStatus() {
    return httpClient.get<LLMStatusDTO>('/api/settings/llm/status');
  }
};
