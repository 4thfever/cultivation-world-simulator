import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import LLMConfigPanel from '@/components/game/panels/system/LLMConfigPanel.vue'
import { createI18n } from 'vue-i18n'
import llmMessages from '@/locales/zh-CN/llm.json'
import uiMessages from '@/locales/zh-CN/ui.json'

// Mock API
vi.mock('@/api', () => ({
  llmApi: {
    fetchConfig: vi.fn().mockResolvedValue({
      base_url: 'http://localhost',
      model_name: 'test',
      fast_model_name: 'test-fast',
      mode: 'default',
      max_concurrent_requests: 10,
      has_api_key: true
    }),
    testConnection: vi.fn().mockResolvedValue(true),
    saveConfig: vi.fn().mockResolvedValue(true)
  }
}))

// Mock naive-ui
vi.mock('naive-ui', () => ({
  useMessage: () => ({
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  }),
  useDialog: () => ({
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  })
}))

describe('LLMConfigPanel', () => {
  const i18n = createI18n({
    legacy: false,
    locale: 'zh-CN',
    messages: {
      'zh-CN': {
        llm: llmMessages,
        ui: uiMessages
      }
    }
  })

  it('should render successfully', () => {
    const wrapper = mount(LLMConfigPanel, {
      global: {
        plugins: [i18n]
      }
    })
    expect(wrapper.exists()).toBe(true)
  })
})
