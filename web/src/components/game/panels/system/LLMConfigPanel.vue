<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useLlmConfigPanel } from '@/composables/useLlmConfigPanel'
import xIcon from '@/assets/icons/ui/lucide/x.svg'

const { t } = useI18n()

const emit = defineEmits<{
  (e: 'config-saved'): void
}>()

const {
  loading,
  testing,
  showHelpModal,
  hasSavedApiKey,
  llmConfigError,
  config,
  modeOptions,
  apiFormatOptions,
  presets,
  applyPreset,
  handleTestAndSave,
} = useLlmConfigPanel(() => emit('config-saved'))
</script>

<template>
  <div class="llm-panel">
    <div v-if="loading" class="loading">{{ t('llm.loading') }}</div>
    <div v-else class="config-form">
      <div v-if="llmConfigError" class="error-banner">
        {{ llmConfigError }}
      </div>
      
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
            <span v-if="preset.badge" :class="['badge', preset.badge]">{{ t(`llm.badges.${preset.badge}`) }}</span>
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
            :placeholder="hasSavedApiKey ? t('ui.saved_secret_keep_empty') : t('llm.placeholders.api_key')"
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
          <label>{{ t('llm.labels.api_format') }}</label>
          <div class="format-options">
            <label
              v-for="opt in apiFormatOptions"
              :key="opt.value"
              class="format-radio"
              :class="{ active: config.api_format === opt.value }"
            >
              <input
                type="radio"
                v-model="config.api_format"
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
          <button class="close-btn" :aria-label="t('ui.close')" @click="showHelpModal = false">
            <span class="close-icon" :style="{ '--icon-url': `url(${xIcon})` }" aria-hidden="true"></span>
          </button>
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
                <h5>Qwen 3.5 Plus / Flash</h5>
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
               <li><a href="https://platform.minimaxi.com/" target="_blank">{{ t('llm.help_links.minimax') }}</a></li>
               <li><a href="https://longcat.chat/platform/docs/zh/" target="_blank">{{ t('llm.help_links.longcat') }}</a></li>
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

.error-banner {
  background: rgba(155, 48, 48, 0.18);
  border: 1px solid rgba(225, 92, 92, 0.42);
  border-radius: 0.35em;
  color: #f0b7b7;
  line-height: 1.45;
  margin-bottom: 1em;
  max-height: 7em;
  overflow: auto;
  padding: 0.75em 0.9em;
  word-break: break-word;
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
  position: relative;
  overflow: visible;
}

.preset-btn .badge {
  position: absolute;
  top: -6px;
  right: -8px;
  font-size: 0.7em;
  padding: 0.1em 0.4em;
  border-radius: 0.5em;
  font-weight: bold;
  pointer-events: none;
  z-index: 1;
}

.preset-btn .badge.recommended {
  background: #f39c12;
  color: #fff;
  border: 1px solid #e67e22;
}

.preset-btn .badge.free {
  background: #2ecc71;
  color: #fff;
  border: 1px solid #27ae60;
}

.preset-btn .badge.local {
  background: #3498db;
  color: #fff;
  border: 1px solid #2980b9;
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

.format-options {
  display: flex;
  flex-direction: row;
  gap: 0.5em;
}

.format-radio {
  display: flex;
  background: #222;
  border: 1px solid #333;
  padding: 0.35em 0.65em;
  border-radius: 0.3em;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
  flex-direction: column;
  align-items: center;
  min-width: 0;
}

.format-radio:hover {
  background: #2a2a2a;
}

.format-radio.active {
  background: #1a2a3a;
  border-color: #4a9eff;
}

.format-options .radio-content {
  display: flex;
  flex-direction: column;
  gap: 0.12em;
}

.format-options .radio-label {
  font-size: 0.82em;
  font-weight: 600;
  line-height: 1.2;
}

.format-options .radio-desc {
  font-size: 0.72em;
  color: #8d8d8d;
  line-height: 1.2;
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
  cursor: pointer;
  transition: color 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.2em;
}

.close-btn:hover {
  color: #fff;
}

.close-icon {
  width: 1.1em;
  height: 1.1em;
  display: inline-block;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
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
