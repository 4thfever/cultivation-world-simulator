<script setup lang="ts">
import type { LLMConfigDTO } from '@/types/api'

type ApiFormatOption = {
  label: string
  desc: string
  value: LLMConfigDTO['api_format']
}

defineProps<{
  title: string
  config: LLMConfigDTO
  apiFormatOptions: ApiFormatOption[]
  apiKeyLabel: string
  apiKeyHelpLabel: string
  apiKeyPlaceholder: string
  showSavedApiKeyMask: boolean
  hasSavedApiKey: boolean
  savedApiKeyHint: string
  clearSavedKeyLabel: string
  testing: boolean
  baseUrlLabel: string
  baseUrlPlaceholder: string
  apiFormatLabel: string
  maxConcurrentRequestsLabel: string
  maxConcurrentRequestsDesc: string
  maxConcurrentRequestsPlaceholder: string
}>()

const emit = defineEmits<{
  (e: 'open-help'): void
  (e: 'api-key-focus'): void
  (e: 'api-key-blur'): void
  (e: 'clear-saved-key'): void
}>()
</script>

<template>
  <div class="section">
    <div class="section-title">{{ title }}</div>

    <div class="form-item">
      <div class="label-row">
        <label>{{ apiKeyLabel }}</label>
        <button class="help-btn" @click="emit('open-help')">{{ apiKeyHelpLabel }}</button>
      </div>
      <div class="api-key-input-wrap" :class="{ 'has-mask': showSavedApiKeyMask }">
        <input
          v-model="config.api_key"
          type="password"
          :placeholder="apiKeyPlaceholder"
          class="input-field"
          @focus="emit('api-key-focus')"
          @blur="emit('api-key-blur')"
        />
        <div v-if="showSavedApiKeyMask" class="saved-key-mask" aria-hidden="true">
          ********************
        </div>
      </div>
      <div v-if="hasSavedApiKey" class="secret-status-row">
        <span>{{ savedApiKeyHint }}</span>
        <button
          type="button"
          class="clear-secret-btn"
          :disabled="testing"
          @click="emit('clear-saved-key')"
        >
          {{ clearSavedKeyLabel }}
        </button>
      </div>
    </div>

    <div class="form-item">
      <label>{{ baseUrlLabel }}</label>
      <input
        v-model="config.base_url"
        type="text"
        :placeholder="baseUrlPlaceholder"
        class="input-field"
      />
    </div>

    <div class="form-item">
      <label>{{ apiFormatLabel }}</label>
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
      <label>{{ maxConcurrentRequestsLabel }}</label>
      <div class="desc">{{ maxConcurrentRequestsDesc }}</div>
      <input
        v-model.number="config.max_concurrent_requests"
        type="number"
        min="1"
        max="50"
        :placeholder="maxConcurrentRequestsPlaceholder"
        class="input-field"
      />
    </div>
  </div>
</template>

<style scoped>
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

.api-key-input-wrap {
  position: relative;
}

.api-key-input-wrap .input-field {
  position: relative;
  z-index: 1;
}

.api-key-input-wrap.has-mask .input-field::placeholder {
  color: transparent;
}

.saved-key-mask {
  align-items: center;
  bottom: 1px;
  color: #b9c0c8;
  display: flex;
  font-family: monospace;
  font-size: 0.9em;
  left: 0.8em;
  letter-spacing: 0;
  pointer-events: none;
  position: absolute;
  top: 1px;
  z-index: 2;
}

.secret-status-row {
  align-items: center;
  display: flex;
  gap: 0.8em;
  justify-content: space-between;
  margin-top: 0.45em;
}

.secret-status-row span {
  color: #7f98ad;
  font-size: 0.78em;
  line-height: 1.35;
}

.clear-secret-btn {
  background: transparent;
  border: 1px solid #4c3b3b;
  border-radius: 0.3em;
  color: #d49b9b;
  cursor: pointer;
  flex: 0 0 auto;
  font-size: 0.78em;
  padding: 0.25em 0.65em;
  transition: all 0.2s;
}

.clear-secret-btn:hover:not(:disabled) {
  background: rgba(150, 58, 58, 0.18);
  border-color: #865454;
  color: #f0b7b7;
}

.clear-secret-btn:disabled {
  color: #666;
  cursor: not-allowed;
  opacity: 0.65;
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
  border-color: #4a9eff;
  background: rgba(74, 158, 255, 0.1);
}

.hidden-radio {
  display: none;
}

.radio-content {
  flex: 1;
}

.radio-label {
  color: #eee;
  font-weight: bold;
  margin-bottom: 0.3em;
}

.radio-desc {
  color: #888;
  font-size: 0.85em;
  line-height: 1.4;
}
</style>
