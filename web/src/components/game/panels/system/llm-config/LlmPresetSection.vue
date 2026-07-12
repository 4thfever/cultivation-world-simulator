<script setup lang="ts">
import type { LlmPreset } from '@/composables/useLlmConfigPanel'

defineProps<{
  title: string
  presets: LlmPreset[]
  badgeLabel: (badge: string) => string
}>()

const emit = defineEmits<{
  (e: 'apply', preset: LlmPreset): void
}>()
</script>

<template>
  <div class="section">
    <div class="section-title">{{ title }}</div>
    <div class="preset-buttons">
      <button
        v-for="preset in presets"
        :key="preset.name"
        class="preset-btn"
        @click="emit('apply', preset)"
      >
        {{ preset.name }}
        <span v-if="preset.badge" :class="['badge', preset.badge]">{{ badgeLabel(preset.badge) }}</span>
      </button>
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

.preset-btn:hover {
  background: #444;
  border-color: #666;
}

.badge {
  position: absolute;
  top: -0.7em;
  right: -0.7em;
  font-size: 0.65em;
  padding: 0.1em 0.4em;
  border-radius: 999px;
  color: #fff;
  background: #666;
  pointer-events: none;
}

.badge.local {
  background: #2f7d32;
}

.badge.key {
  background: #b26a00;
}
</style>
