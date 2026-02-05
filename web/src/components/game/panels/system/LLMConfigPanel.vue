<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { llmApi } from '../../../../api'
import type { LLMConfigDTO } from '../../../../types/api'
import { useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const message = useMessage()
const loading = ref(false)
const testing = ref(false)
const showHelpModal = ref(false)

const config = ref<LLMConfigDTO>({
  base_url: '',
  api_key: '',
  model_name: '',
  fast_model_name: '',
  mode: 'default',
  max_concurrent_requests: 10
})

const modeOptions = computed(() => [
  { label: t('llm.modes.default'), value: 'default', desc: t('llm.modes.default_desc') },
  { label: t('llm.modes.normal'), value: 'normal', desc: t('llm.modes.normal_desc') },
  { label: t('llm.modes.fast'), value: 'fast', desc: t('llm.modes.fast_desc') }
])

const presets = computed(() => [
  {
    name: t('llm.presets.openai'),
    base_url: 'https://api.openai.com/v1',
    model_name: 'gpt-4o',
    fast_model_name: 'gpt-4o-mini'
  },
  {
    name: t('llm.presets.qwen'),
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model_name: 'qwen-plus',
    fast_model_name: 'qwen-flash'
  },
  {
    name: t('llm.presets.deepseek'),
    base_url: 'https://api.deepseek.com',
    model_name: 'deepseek-chat',
    fast_model_name: 'deepseek-chat'
  },
  {
    name: t('llm.presets.siliconflow'),
    base_url: 'https://api.siliconflow.cn/v1',
    model_name: 'Qwen/Qwen2.5-72B-Instruct',
    fast_model_name: 'Qwen/Qwen2.5-7B-Instruct'
  },
  {
    name: t('llm.presets.openrouter'),
    base_url: 'https://openrouter.ai/api/v1',
    model_name: 'anthropic/claude-3.5-sonnet',
    fast_model_name: 'google/gemini-3-flash'
  },
  {
    name: t('llm.presets.gemini'),
    // Note: The `/openai` suffix is required to use Google's OpenAI-compatible API.
    // Our backend (src/utils/llm/client.py) uses OpenAI-compatible format with
    // Bearer token auth and /chat/completions endpoint, so we need this suffix
    // to make Google API accept OpenAI-style requests instead of native Gemini format.
    base_url: 'https://generativelanguage.googleapis.com/v1beta/openai/',
    model_name: 'gemini-3-pro-preview',
    fast_model_name: 'gemini-3-flash-preview'
  },
  {
    name: t('llm.presets.ollama'),
    base_url: 'http://localhost:11434/v1',
    model_name: 'qwen2.5:7b',
    fast_model_name: 'qwen2.5:7b',
    isLocal: true
  }
])

async function fetchConfig() {
  loading.value = true
  try {
    const res = await llmApi.fetchConfig()
    // 确保 API Key 在前端展示为空，增加安全性提示
    config.value = { ...res, api_key: '' }
  } catch (e) {
    message.error(t('llm.fetch_failed'))
  } finally {
    loading.value = false
  }
}

function applyPreset(preset: any) {
  config.value.base_url = preset.base_url
  config.value.model_name = preset.model_name
  config.value.fast_model_name = preset.fast_model_name
  // Ollama doesn't require a real API key, auto-fill a placeholder.
  if ('isLocal' in preset && preset.isLocal) {
    config.value.api_key = 'ollama'
    message.info(t('llm.preset_applied', { name: preset.name, extra: t('llm.preset_extra_local') }))
  } else {
    config.value.api_key = ''
    message.info(t('llm.preset_applied', { name: preset.name, extra: t('llm.preset_extra_key') }))
  }
}

const emit = defineEmits<{
  (e: 'config-saved'): void
}>()

async function handleTestAndSave() {
  if (!config.value.base_url) {
    message.warning(t('llm.base_url_required'))
    return
  }

  testing.value = true
  try {
    // 1. 测试连接
    await llmApi.testConnection(config.value)
    message.success(t('llm.test_success'))
    
    // 2. 保存配置
    await llmApi.saveConfig(config.value)
    message.success(t('llm.save_success'))
    emit('config-saved')
  } catch (e: any) {
    const errorMsg = e.response?.data?.detail || e.message
    message.error(t('llm.test_save_failed', { error: errorMsg }))
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  fetchConfig()
})
</script>

<template>
  <div class="llm-panel">
    <div v-if="loading" class="loading">{{ t('llm.loading') }}</div>
    <div v-else class="config-form">
      
      <!-- 预设按钮 -->
      <div class="section">
        <div class="section-title">{{ t('llm.sections.quick_fill') }}</div>
        <div class="preset-buttons">
          <button 
            v-for="preset in presets" 
            :key="preset.name"
            class="preset-btn"
            @click="applyPreset(preset)"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>

      <!-- 核心配置 -->
      <div class="section">
        <div class="section-title">{{ t('llm.sections.api_config') }}</div>
        
        <div class="form-item">
          <div class="label-row">
            <label>{{ t('llm.labels.api_key') }}</label>
            <button class="help-btn" @click="showHelpModal = true">{{ t('llm.labels.what_is_api') }}</button>
          </div>
          <input 
            v-model="config.api_key" 
            type="password" 
            :placeholder="t('llm.placeholders.api_key')"
            class="input-field"
          />
        </div>

        <div class="form-item">
          <label>{{ t('llm.labels.base_url') }}</label>
          <input 
            v-model="config.base_url" 
            type="text" 
            :placeholder="t('llm.placeholders.base_url')"
            class="input-field"
          />
        </div>

        <div class="form-item">
          <label>{{ t('llm.labels.max_concurrent_requests') }}</label>
          <div class="desc">{{ t('llm.descs.max_concurrent_requests') }}</div>
          <input 
            v-model.number="config.max_concurrent_requests" 
            type="number" 
            min="1"
            max="50"
            :placeholder="t('llm.placeholders.max_concurrent_requests')"
            class="input-field"
          />
        </div>
      </div>

      <!-- 模型配置 -->
      <div class="section">
        <div class="section-title">{{ t('llm.sections.model_selection') }}</div>
        
        <div class="form-item">
          <label>{{ t('llm.labels.normal_model') }}</label>
          <div class="desc">{{ t('llm.descs.normal_model') }}</div>
          <input 
            v-model="config.model_name" 
            type="text" 
            :placeholder="t('llm.placeholders.normal_model')"
            class="input-field"
          />
        </div>

        <div class="form-item">
          <label>{{ t('llm.labels.fast_model') }}</label>
          <div class="desc">{{ t('llm.descs.fast_model') }}</div>
          <input 
            v-model="config.fast_model_name" 
            type="text" 
            :placeholder="t('llm.placeholders.fast_model')"
            class="input-field"
          />
        </div>
      </div>

      <!-- 模式选择 -->
      <div class="section">
        <div class="section-title">{{ t('llm.sections.run_mode') }}</div>
        <div class="mode-options horizontal">
          <label 
            v-for="opt in modeOptions" 
            :key="opt.value"
            class="mode-radio"
            :class="{ active: config.mode === opt.value }"
          >
            <input 
              type="radio" 
              v-model="config.mode" 
              :value="opt.value"
              class="hidden-radio"
            />
            <div class="radio-content">
              <div class="radio-label">{{ opt.label }}</div>
              <div class="radio-desc">{{ opt.desc }}</div>
            </div>
          </label>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="action-bar">
        <button 
          class="save-btn" 
          :disabled="testing"
          @click="handleTestAndSave"
        >
          {{ testing ? t('llm.actions.testing') : t('llm.actions.test_and_save') }}
        </button>
      </div>

    </div>

    <!-- 帮助弹窗 -->
    <div v-if="showHelpModal" class="modal-overlay" @click.self="showHelpModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ t('llm.help.title') }}</h3>
          <button class="close-btn" @click="showHelpModal = false">×</button>
        </div>
        
        <div class="modal-body">
          <div class="help-section">
            <h4>{{ t('llm.help.q1_title') }}</h4>
            <p>
              {{ t('llm.help.q1_content') }}
            </p>
          </div>

          <div class="help-section">
            <h4>{{ t('llm.help.q2_title') }}</h4>
            <div class="model-cards">
              <div class="card">
                <h5>Qwen-Plus / Fast</h5>
                <p>{{ t('llm.help.q2_qwen') }}</p>
              </div>
              <div class="card">
                <h5>DeepSeek V3</h5>
                <p>{{ t('llm.help.q2_deepseek') }}</p>
              </div>
              <div class="card">
                <h5>Gemini 3 Pro / Fast</h5>
                <p>{{ t('llm.help.q2_gemini') }}</p>
              </div>
            </div>
          </div>

          <div class="help-section">
            <h4>{{ t('llm.help.q3_title') }}</h4>
            <p>{{ t('llm.help.q3_content') }}</p>
            <div class="format-note">
              <p>{{ t('llm.help.q3_format_note') }}</p>
            </div>
            <div class="code-block">
              <p>{{ t('llm.help.q3_base_url') }}</p>
              <p>{{ t('llm.help.q3_api_key') }}</p>
              <p>{{ t('llm.help.q3_model_name') }}</p>
            </div>
          </div>

          <div class="help-section">
            <h4>{{ t('llm.help.q4_title') }}</h4>
            <ul class="link-list">
               <li><a href="https://platform.openai.com/" target="_blank">{{ t('llm.help_links.openai') }}</a></li>
               <li><a href="https://bailian.console.aliyun.com/" target="_blank">{{ t('llm.help_links.qwen') }}</a></li>
               <li><a href="https://platform.deepseek.com/" target="_blank">{{ t('llm.help_links.deepseek') }}</a></li>
               <li><a href="https://openrouter.ai/" target="_blank">{{ t('llm.help_links.openrouter') }}</a></li>
               <li><a href="https://cloud.siliconflow.cn/" target="_blank">{{ t('llm.help_links.siliconflow') }}</a></li>
               <li><a href="https://aistudio.google.com/" target="_blank">{{ t('llm.help_links.gemini') }}</a></li>
            </ul>
          </div>

          <div class="help-section">
            <h4>{{ t('llm.help.q5_title') }}</h4>
            <p>
              {{ t('llm.help.q5_p1') }}
            </p>
            <p>
              {{ t('llm.help.q5_p2') }}
            </p>
          </div>
        </div>

        <div class="modal-footer">
          <button class="confirm-btn" @click="showHelpModal = false">{{ t('llm.help.confirm') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.llm-panel {
  height: 100%;
  overflow-y: auto;
  padding: 0 0.8em;
}

.loading {
  text-align: center;
  color: #888;
  padding: 3em;
}

.section {
  margin-bottom: 1.5em;
}

.section-title {
  font-size: 1em;
  font-weight: bold;
  color: #ddd;
  margin-bottom: 0.8em;
  border-left: 0.2em solid #4a9eff;
  padding-left: 0.5em;
}

.preset-buttons {
  display: flex;
  gap: 0.8em;
  flex-wrap: wrap;
}

.preset-btn {
  background: #333;
  border: 1px solid #444;
  color: #ccc;
  padding: 0.4em 0.8em;
  border-radius: 0.3em;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.85em;
}

.preset-btn:hover {
  background: #444;
  border-color: #666;
  color: #fff;
}

.form-item {
  margin-bottom: 1.2em;
}

.form-item label {
  display: block;
  font-size: 0.9em;
  color: #bbb;
  margin-bottom: 0.4em;
}

.form-item .desc {
  font-size: 0.8em;
  color: #666;
  margin-bottom: 0.4em;
}

.input-field {
  width: 100%;
  background: #222;
  border: 1px solid #444;
  color: #ddd;
  padding: 0.6em 0.8em;
  border-radius: 0.3em;
  font-family: monospace;
  font-size: 0.9em;
}

.input-field:focus {
  outline: none;
  border-color: #4a9eff;
  background: #1a1a1a;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4em;
}

.help-btn {
  background: none;
  border: 1px solid #444;
  color: #888;
  font-size: 0.8em;
  padding: 0.2em 0.6em;
  border-radius: 1em;
  cursor: pointer;
  transition: all 0.2s;
}

.help-btn:hover {
  border-color: #666;
  color: #bbb;
  background: #2a2a2a;
}

.mode-options.horizontal {
  display: flex;
  flex-direction: row;
  gap: 0.8em;
}

.mode-options.horizontal .mode-radio {
  flex: 1;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0.8em 0.4em;
}

.mode-radio {
  display: flex;
  background: #222;
  border: 1px solid #333;
  padding: 0.8em;
  border-radius: 0.3em;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-radio:hover {
  background: #2a2a2a;
}

.mode-radio.active {
  background: #1a2a3a;
  border-color: #4a9eff;
}

.hidden-radio {
  display: none;
}

.radio-content {
  flex: 1;
}

.radio-label {
  color: #ddd;
  font-size: 0.9em;
  font-weight: bold;
  margin-bottom: 0.3em;
}

.radio-desc {
  color: #777;
  font-size: 0.8em;
  line-height: 1.3;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.85);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background: #0f1115;
  border: 1px solid #333;
  border-radius: 0.8em;
  width: 50em;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1.5em 3em rgba(0,0,0,0.7);
  overflow: hidden;
  font-size: 1rem; /* 重置 modal 内部字体，避免过大，或者保留继承 */
}

.modal-header {
  padding: 1.2em 1.5em;
  border-bottom: 1px solid #222;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(to bottom, #1a1c22, #0f1115);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2em;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 0.5em;
}

.modal-header h3::before {
  content: "?";
  display: inline-flex;
  width: 1.4em;
  height: 1.4em;
  border: 1px solid #00e0b0;
  color: #00e0b0;
  border-radius: 50%;
  font-size: 0.9em;
  align-items: center;
  justify-content: center;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 1.5em;
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #fff;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5em;
  color: #aaa;
}

.help-section {
  margin-bottom: 2em;
}

.help-section h4 {
  color: #6da;
  font-size: 1.1em;
  margin: 0 0 0.8em 0;
}

.help-section p {
  line-height: 1.6;
  margin: 0 0 0.6em 0;
  font-size: 0.95em;
}

.model-cards {
  display: flex;
  gap: 0.8em;
  margin-top: 0.8em;
}

.card {
  flex: 1;
  background: #16181d;
  border: 1px solid #333;
  border-radius: 0.5em;
  padding: 0.8em;
}

.card h5 {
  color: #8a9eff;
  margin: 0 0 0.5em 0;
  font-size: 0.95em;
}

.card p {
  font-size: 0.85em;
  color: #777;
  margin: 0;
}

.format-note {
  background: #1a1f2e;
  border: 1px solid #4a5a7a;
  border-left: 0.3em solid #ffa500;
  border-radius: 0.5em;
  padding: 0.8em 1em;
  margin: 0.8em 0;
}

.format-note p {
  margin: 0;
  color: #ffd700;
  font-size: 0.9em;
  line-height: 1.5;
}

.code-block {
  background: #111;
  border: 1px solid #2a2a2a;
  border-radius: 0.5em;
  padding: 1em;
  font-family: monospace;
}

.code-block p {
  margin-bottom: 0.5em;
}

.code-block p:last-child {
  margin-bottom: 0;
}

.code-block strong {
  color: #00e0b0;
}

.code-block code {
  background: #333;
  padding: 0.1em 0.4em;
  border-radius: 0.2em;
  color: #ff79c6;
}

.link-list {
  list-style: none;
  padding: 0;
  margin: 0;
  background: #16181d;
  border: 1px solid #333;
  border-radius: 0.5em;
}

.link-list li {
  border-bottom: 1px solid #222;
}

.link-list li:last-child {
  border-bottom: none;
}

.link-list a {
  display: flex;
  justify-content: space-between;
  padding: 0.8em 1em;
  color: #ddd;
  text-decoration: none;
  font-size: 0.95em;
  transition: background 0.2s;
}

.link-list a:hover {
  background: #1f2229;
}

.link-list a::after {
  content: "↗";
  color: #666;
}

.modal-footer {
  padding: 1em 1.5em;
  border-top: 1px solid #222;
  background: #0f1115;
}

.confirm-btn {
  width: 100%;
  background: #0099cc;
  color: white;
  border: none;
  padding: 0.8em;
  border-radius: 0.4em;
  font-size: 1em;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}

.confirm-btn:hover {
  background: #0088bb;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  padding-bottom: 1.5em;
}

.save-btn {
  background: #2a8a4a;
  color: #fff;
  border: none;
  padding: 0.7em 1.5em;
  border-radius: 0.3em;
  font-size: 0.95em;
  cursor: pointer;
  transition: background 0.2s;
}

.save-btn:hover:not(:disabled) {
  background: #3aa85a;
}

.save-btn:disabled {
  background: #33443a;
  color: #888;
  cursor: not-allowed;
}
</style>
