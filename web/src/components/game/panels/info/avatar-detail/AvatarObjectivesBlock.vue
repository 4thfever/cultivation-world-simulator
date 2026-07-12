<script setup lang="ts">
import type { AvatarDetail } from '@/types/core'

defineProps<{
  data: AvatarDetail
  noneText: string
  labels: {
    backstory: string
    fate: string
    longTermObjective: string
    shortTermObjective: string
  }
}>()
</script>

<template>
  <div class="objectives-banner">
    <div class="objective-item backstory-item" v-if="data.backstory">
      <span class="label">{{ labels.backstory }}</span>
      <span class="value">{{ data.backstory }}</span>
    </div>
    <div class="objective-item fate-item" v-if="data.fate_revelation">
      <span class="label">{{ labels.fate }}</span>
      <span class="value fate-value">
        <span class="fate-oracle">『{{ data.fate_revelation.oracle_text }}』</span>
      </span>
    </div>
    <div class="objective-item">
      <span class="label">{{ labels.longTermObjective }}</span>
      <span class="value">{{ data.long_term_objective || noneText }}</span>
    </div>
    <div class="objective-item">
      <span class="label">{{ labels.shortTermObjective }}</span>
      <span class="value">{{ data.short_term_objective || noneText }}</span>
    </div>
  </div>
</template>

<style scoped>
.objectives-banner {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  margin-bottom: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.objective-item {
  display: flex;
  gap: 8px;
  font-size: 12px;
  line-height: 1.4;
}

.objective-item .label {
  color: #888;
  white-space: nowrap;
  font-weight: bold;
}

.objective-item .value {
  color: #ccc;
}

.fate-value {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.fate-oracle {
  color: #d8c39a;
  font-weight: 600;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
</style>
