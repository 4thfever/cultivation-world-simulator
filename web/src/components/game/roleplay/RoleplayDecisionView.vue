<script setup lang="ts">
import type { RoleplayInteractionRecordDTO } from '@/types/api'

import RoleplayInteractionHistory from './RoleplayInteractionHistory.vue'

const props = defineProps<{
  description: string
  modelValue: string
  errorText: string
  isSubmitting: boolean
  submitText: string
  interactionHistory: RoleplayInteractionRecordDTO[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  submit: []
}>()

function handleInput(event: Event) {
  emit('update:modelValue', (event.target as HTMLTextAreaElement).value)
}

function handleSubmit() {
  if (props.isSubmitting || !props.modelValue.trim()) return
  emit('submit')
}
</script>

<template>
  <div class="roleplay-dock__console">
    <div class="roleplay-dock__request-intro">{{ description }}</div>
    <RoleplayInteractionHistory :items="interactionHistory" />
    <textarea
      class="roleplay-dock__input"
      rows="3"
      placeholder="输入角色的下一步意图，例如：先调息恢复，再去附近探索。"
      :value="modelValue"
      @input="handleInput"
    />
    <div class="roleplay-dock__actions">
      <div v-if="errorText" class="roleplay-dock__error">{{ errorText }}</div>
      <button
        class="roleplay-dock__submit"
        :disabled="isSubmitting || !modelValue.trim()"
        @click="handleSubmit"
      >
        <span v-if="isSubmitting" class="roleplay-dock__spinner" aria-hidden="true"></span>
        {{ submitText }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.roleplay-dock__console {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.roleplay-dock__request-intro {
  font-size: 12px;
  line-height: 1.5;
  color: #c4b89d;
}

.roleplay-dock__input {
  width: 100%;
  min-height: 72px;
  resize: none;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(4, 4, 4, 0.92);
  color: #f4f1e8;
  padding: 10px 12px;
  font: inherit;
}

.roleplay-dock__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.roleplay-dock__submit {
  border: 1px solid rgba(208, 180, 124, 0.26);
  border-radius: 8px;
  padding: 6px 10px;
  white-space: nowrap;
  font-size: 12px;
  color: #f6ecd2;
  background: rgba(86, 61, 23, 0.78);
  cursor: pointer;
}

.roleplay-dock__submit:disabled {
  cursor: default;
  opacity: 0.62;
}

.roleplay-dock__error {
  font-size: 12px;
  line-height: 1.6;
  color: #ff9a9a;
}

.roleplay-dock__spinner {
  width: 12px;
  height: 12px;
  margin-right: 6px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: roleplay-dock-spin 0.7s linear infinite;
  display: inline-block;
  vertical-align: -2px;
}

@keyframes roleplay-dock-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
