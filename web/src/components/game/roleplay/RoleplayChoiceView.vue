<script setup lang="ts">
import { onMounted, ref } from 'vue'

type ChoiceOption = {
  key: string
  title: string
  description: string
  variant?: 'accept' | 'reject' | 'default'
}

const props = defineProps<{
  description: string
  options: ChoiceOption[]
  errorText: string
  isSubmitting: boolean
  submittingText: string
}>()

const emit = defineEmits<{
  submit: [selectedKey: string]
}>()

const choiceListRef = ref<HTMLElement | null>(null)

function getChoiceVariant(option: ChoiceOption): 'accept' | 'reject' | 'default' {
  return option.variant ?? 'default'
}

function handleSubmit(selectedKey: string) {
  if (props.isSubmitting) return
  emit('submit', selectedKey)
}

function handleChoiceKeydown(event: KeyboardEvent) {
  const index = Number(event.key) - 1
  if (!Number.isInteger(index) || index < 0 || index >= props.options.length) return
  event.preventDefault()
  handleSubmit(props.options[index].key)
}

onMounted(() => {
  choiceListRef.value?.focus()
})
</script>

<template>
  <div class="roleplay-dock__choice-pane">
    <div class="roleplay-dock__request-intro">{{ description }}</div>
    <div
      ref="choiceListRef"
      class="roleplay-dock__choice-list"
      tabindex="0"
      @keydown="handleChoiceKeydown"
    >
      <button
        v-for="option in options"
        :key="option.key"
        class="roleplay-dock__choice"
        :class="`roleplay-dock__choice--${getChoiceVariant(option)}`"
        :disabled="isSubmitting"
        @click="handleSubmit(option.key)"
      >
        <span class="roleplay-dock__choice-title">{{ option.title }}</span>
        <span class="roleplay-dock__choice-desc">{{ option.description }}</span>
      </button>
    </div>
    <div v-if="submittingText" class="roleplay-dock__submitting-hint">
      <span class="roleplay-dock__spinner" aria-hidden="true"></span>
      {{ submittingText }}
    </div>
    <div v-if="errorText" class="roleplay-dock__error">{{ errorText }}</div>
  </div>
</template>

<style scoped>
.roleplay-dock__choice-pane {
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

.roleplay-dock__choice-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  align-items: stretch;
  width: 100%;
  max-width: 680px;
  margin: 0 auto;
  outline: none;
}

.roleplay-dock__choice {
  flex: 1 1 220px;
  max-width: 320px;
  min-height: 68px;
  border: 1px solid rgba(208, 180, 124, 0.26);
  border-radius: 8px;
  padding: 8px 10px;
  text-align: left;
  display: grid;
  gap: 3px;
  color: #f6ecd2;
  background: rgba(86, 61, 23, 0.78);
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.12s ease;
}

.roleplay-dock__choice:hover {
  transform: translateY(-1px);
}

.roleplay-dock__choice:active {
  transform: translateY(0);
}

.roleplay-dock__choice:disabled {
  cursor: default;
  opacity: 0.62;
}

.roleplay-dock__choice--accept {
  border-color: rgba(98, 190, 133, 0.42);
  background: linear-gradient(180deg, rgba(62, 116, 81, 0.56), rgba(42, 78, 56, 0.82));
}

.roleplay-dock__choice--accept:hover {
  border-color: rgba(126, 216, 160, 0.64);
  background: linear-gradient(180deg, rgba(72, 132, 92, 0.66), rgba(50, 93, 67, 0.9));
}

.roleplay-dock__choice--reject {
  border-color: rgba(213, 108, 108, 0.45);
  background: linear-gradient(180deg, rgba(130, 58, 58, 0.55), rgba(94, 42, 42, 0.82));
}

.roleplay-dock__choice--reject:hover {
  border-color: rgba(232, 140, 140, 0.64);
  background: linear-gradient(180deg, rgba(148, 66, 66, 0.66), rgba(108, 48, 48, 0.9));
}

.roleplay-dock__choice-title {
  font-size: 12px;
  font-weight: 700;
}

.roleplay-dock__choice-desc {
  font-size: 11px;
  line-height: 1.4;
  color: #efe7d5;
}

.roleplay-dock__submitting-hint {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
  font-size: 12px;
  color: #cdb78c;
  padding: 2px 0;
}

.roleplay-dock__error {
  font-size: 12px;
  line-height: 1.6;
  color: #ff9a9a;
}

.roleplay-dock__spinner {
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: roleplay-dock-spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes roleplay-dock-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 640px) {
  .roleplay-dock__choice {
    flex-basis: 100%;
    max-width: none;
  }
}
</style>
