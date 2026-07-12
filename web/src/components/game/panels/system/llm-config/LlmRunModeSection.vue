<script setup lang="ts">
import type { LLMConfigDTO } from '@/types/api'

type ModeOption = {
  label: string
  desc: string
  value: LLMConfigDTO['mode']
}

defineProps<{
  title: string
  modelValue: LLMConfigDTO['mode']
  options: ModeOption[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: LLMConfigDTO['mode']): void
}>()
</script>

<template>
  <div class="section">
    <div class="section-title">{{ title }}</div>
    <div class="mode-options horizontal">
      <label
        v-for="opt in options"
        :key="opt.value"
        class="mode-radio"
        :class="{ active: modelValue === opt.value }"
      >
        <input
          type="radio"
          :checked="modelValue === opt.value"
          :value="opt.value"
          class="hidden-radio"
          @change="emit('update:modelValue', opt.value)"
        />
        <div class="radio-content">
          <div class="radio-label">{{ opt.label }}</div>
          <div class="radio-desc">{{ opt.desc }}</div>
        </div>
      </label>
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

.mode-options {
  display: flex;
  flex-direction: column;
  gap: 0.8em;
}

.mode-options.horizontal {
  flex-direction: row;
}

.mode-radio {
  flex: 1;
  display: flex;
  gap: 0.8em;
  padding: 0.8em;
  border: 1px solid #333;
  border-radius: 0.4em;
  background: #1a1a1a;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-radio:hover {
  background: #222;
}

.mode-radio.active {
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
