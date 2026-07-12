<script setup lang="ts">
import checkIcon from '@/assets/icons/ui/lucide/check.svg'

defineProps<{
  modelValue: string
  title: string
  placeholder: string
  confirmText: string
  cancelText: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()
</script>

<template>
  <div class="modal-overlay">
    <div class="modal">
      <h3>{{ title }}</h3>
      <textarea
        :value="modelValue"
        :placeholder="placeholder"
        @input="emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
      ></textarea>
      <div class="modal-footer">
        <button class="btn primary" @click="emit('confirm')">
          <span class="button-icon" :style="{ '--icon-url': `url(${checkIcon})` }" aria-hidden="true"></span>
          {{ confirmText }}
        </button>
        <button class="btn" @click="emit('cancel')">{{ cancelText }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: absolute;
  top: 0;
  left: -16px;
  right: -16px;
  bottom: -16px;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  width: 280px;
  background: #222;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal h3 {
  margin: 0;
  font-size: 14px;
  color: #ddd;
}

.modal textarea {
  height: 100px;
  background: #111;
  border: 1px solid #444;
  color: #eee;
  padding: 8px;
  resize: none;
}

.modal-footer {
  display: flex;
  gap: 10px;
}

.btn {
  flex: 1;
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
  color: #ccc;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn.primary {
  background: #177ddc;
  color: white;
  border: none;
}

.btn.primary:hover {
  background: #1890ff;
}

.button-icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
  flex-shrink: 0;
}
</style>
