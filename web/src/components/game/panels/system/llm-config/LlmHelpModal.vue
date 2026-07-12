<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import xIcon from '@/assets/icons/ui/lucide/x.svg'

const { t } = useI18n()

const emit = defineEmits<{
  (e: 'close'): void
}>()
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ t('llm.help.title') }}</h3>
        <button class="close-btn" :aria-label="t('ui.close')" @click="emit('close')">
          <span class="close-icon" :style="{ '--icon-url': `url(${xIcon})` }" aria-hidden="true"></span>
        </button>
      </div>

      <div class="modal-body">
        <div class="help-section">
          <h4>{{ t('llm.help.q1_title') }}</h4>
          <p>{{ t('llm.help.q1_content') }}</p>
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
          <p>{{ t('llm.help.q5_p1') }}</p>
          <p>{{ t('llm.help.q5_p2') }}</p>
        </div>
      </div>

      <div class="modal-footer">
        <button class="confirm-btn" @click="emit('close')">{{ t('llm.help.confirm') }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2em;
}

.modal-content {
  background: #111;
  border: 1px solid #333;
  border-radius: 0.5em;
  width: min(720px, 100%);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1em 1.5em;
  border-bottom: 1px solid #333;
}

.modal-header h3 {
  margin: 0;
  color: #fff;
}

.close-btn {
  background: transparent;
  border: none;
  color: #aaa;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.25em;
}

.close-icon {
  display: inline-block;
  width: 1.2em;
  height: 1.2em;
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
  padding: 1.5em;
  overflow-y: auto;
}

.help-section {
  margin-bottom: 1.5em;
}

.help-section h4 {
  color: #4a9eff;
  margin: 0 0 0.5em;
}

.help-section p {
  color: #ccc;
  line-height: 1.6;
  margin: 0 0 0.8em;
}

.model-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1em;
}

.card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 0.5em;
  padding: 1em;
}

.card h5 {
  color: #fff;
  margin: 0 0 0.5em;
}

.format-note,
.code-block {
  background: #181818;
  border: 1px solid #333;
  border-radius: 0.5em;
  padding: 1em;
}

.code-block {
  font-family: monospace;
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
</style>
