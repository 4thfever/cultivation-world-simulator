import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDialog, useMessage } from 'naive-ui'
import { storeToRefs } from 'pinia'
import { llmApi } from '@/api'
import type { LLMConfigDTO } from '@/types/api'
import { useUiStore } from '@/stores/ui'

export interface LlmPreset {
  name: string
  base_url: string
  model_name: string
  fast_model_name: string
  api_format: LLMConfigDTO['api_format']
  badge?: 'recommended' | 'free' | 'local'
  isLocal?: boolean
}

const createEmptyConfig = (): LLMConfigDTO => ({
  base_url: '',
  api_key: '',
  model_name: '',
  fast_model_name: '',
  mode: 'default',
  max_concurrent_requests: 10,
  api_format: 'openai',
})

export function useLlmConfigPanel(onConfigSaved: () => void) {
  const { t } = useI18n()
  const message = useMessage()
  const dialog = useDialog()
  const uiStore = useUiStore()
  const { llmConfigError } = storeToRefs(uiStore)
  const loading = ref(false)
  const testing = ref(false)
  const showHelpModal = ref(false)
  const hasSavedApiKey = ref(false)
  const config = ref<LLMConfigDTO>(createEmptyConfig())

  const modeOptions = computed(() => [
    { label: t('llm.modes.default'), value: 'default', desc: t('llm.modes.default_desc') },
    { label: t('llm.modes.normal'), value: 'normal', desc: t('llm.modes.normal_desc') },
    { label: t('llm.modes.fast'), value: 'fast', desc: t('llm.modes.fast_desc') },
  ])

  const apiFormatOptions = computed(() => [
    { label: t('llm.formats.openai'), value: 'openai', desc: t('llm.formats.openai_desc') },
    { label: t('llm.formats.anthropic'), value: 'anthropic', desc: t('llm.formats.anthropic_desc') },
  ])

  const presets = computed<LlmPreset[]>(() => [
    {
      name: t('llm.presets.qwen'),
      base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      model_name: 'qwen3.5-plus',
      fast_model_name: 'qwen3.5-flash',
      api_format: 'openai',
      badge: 'recommended',
    },
    {
      name: t('llm.presets.gemini'),
      base_url: 'https://generativelanguage.googleapis.com/v1beta/openai/',
      model_name: 'gemini-3-pro-preview',
      fast_model_name: 'gemini-3-flash-preview',
      api_format: 'openai',
      badge: 'recommended',
    },
    {
      name: t('llm.presets.openai'),
      base_url: 'https://api.openai.com/v1',
      model_name: 'gpt-4o',
      fast_model_name: 'gpt-4o-mini',
      api_format: 'openai',
    },
    {
      name: t('llm.presets.anthropic'),
      base_url: 'https://api.anthropic.com',
      model_name: 'claude-sonnet-4-20250514',
      fast_model_name: 'claude-haiku-4-20250414',
      api_format: 'anthropic',
    },
    {
      name: t('llm.presets.kimi'),
      base_url: 'https://api.moonshot.cn/v1',
      model_name: 'kimi-k2.5',
      fast_model_name: 'kimi-k2-turbo-preview',
      api_format: 'openai',
    },
    {
      name: t('llm.presets.deepseek'),
      base_url: 'https://api.deepseek.com',
      model_name: 'deepseek-chat',
      fast_model_name: 'deepseek-chat',
      api_format: 'openai',
      badge: 'free',
    },
    {
      name: t('llm.presets.groq'),
      base_url: 'https://api.groq.com/openai/v1',
      model_name: 'llama-3.3-70b-versatile',
      fast_model_name: 'llama-3.1-8b-instant',
      api_format: 'openai',
      badge: 'free',
    },
    {
      name: t('llm.presets.minimax'),
      base_url: 'https://api.minimax.io/v1',
      model_name: 'MiniMax-M2.7',
      fast_model_name: 'MiniMax-M2.5-highspeed',
      api_format: 'openai',
    },
    {
      name: t('llm.presets.longcat'),
      base_url: 'https://api.longcat.chat/openai',
      model_name: 'LongCat-Flash-Chat',
      fast_model_name: 'LongCat-Flash-Lite',
      api_format: 'openai',
      badge: 'free',
    },
    {
      name: t('llm.presets.siliconflow'),
      base_url: 'https://api.siliconflow.cn/v1',
      model_name: 'Qwen/Qwen2.5-72B-Instruct',
      fast_model_name: 'Qwen/Qwen2.5-7B-Instruct',
      api_format: 'openai',
    },
    {
      name: t('llm.presets.openrouter'),
      base_url: 'https://openrouter.ai/api/v1',
      model_name: 'anthropic/claude-3.5-sonnet',
      fast_model_name: 'google/gemini-3-flash',
      api_format: 'openai',
    },
    {
      name: t('llm.presets.ollama'),
      base_url: 'http://localhost:11434/v1',
      model_name: 'qwen2.5:7b',
      fast_model_name: 'qwen2.5:7b',
      api_format: 'openai',
      badge: 'local',
      isLocal: true,
    },
  ])

  async function fetchConfig() {
    loading.value = true
    try {
      const result = await llmApi.fetchConfig()
      hasSavedApiKey.value = result.has_api_key
      config.value = {
        base_url: result.base_url,
        api_key: '',
        model_name: result.model_name,
        fast_model_name: result.fast_model_name,
        mode: result.mode,
        max_concurrent_requests: result.max_concurrent_requests,
        api_format: result.api_format || 'openai',
      }
    } catch {
      message.error(t('llm.fetch_failed'))
    } finally {
      loading.value = false
    }
  }

  function applyPreset(preset: LlmPreset) {
    config.value.base_url = preset.base_url
    config.value.model_name = preset.model_name
    config.value.fast_model_name = preset.fast_model_name
    config.value.api_format = preset.api_format || 'openai'
    if (preset.isLocal) {
      config.value.api_key = 'ollama'
      message.info(t('llm.preset_applied', { name: preset.name, extra: t('llm.preset_extra_local') }))
    } else {
      config.value.api_key = ''
      message.info(t('llm.preset_applied', { name: preset.name, extra: t('llm.preset_extra_key') }))
    }
  }

  async function handleTestAndSave() {
    if (!config.value.base_url) {
      message.warning(t('llm.base_url_required'))
      return
    }

    testing.value = true
    try {
      await llmApi.testConnection(config.value)
      message.success(t('llm.test_success'))
      await llmApi.saveConfig(config.value)
      message.success(t('llm.save_success'))
      uiStore.clearLlmConfigError()
      onConfigSaved()
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : t('llm.test_save_failed_title')
      dialog.error({
        title: t('llm.test_save_failed_title'),
        content: errorMsg,
        positiveText: t('common.confirm'),
      })
    } finally {
      testing.value = false
    }
  }

  onMounted(() => {
    void fetchConfig()
  })

  return {
    loading,
    testing,
    showHelpModal,
    hasSavedApiKey,
    llmConfigError,
    config,
    modeOptions,
    apiFormatOptions,
    presets,
    fetchConfig,
    applyPreset,
    handleTestAndSave,
  }
}
