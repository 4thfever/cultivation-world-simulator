<script setup lang="ts">
import { getEntityColor } from '@/utils/theme';
import type { EffectEntity } from '@/types/core';

defineProps<{
  item: EffectEntity;
  meta?: string; // e.g. "Rank 3" or "Count: 5"
  compact?: boolean;
}>();

defineEmits(['click']);
</script>

<template>
  <div 
    class="entity-row" 
    :class="{ 'compact': compact }"
    @click="$emit('click')"
  >
    <span class="name" :style="{ color: getEntityColor(item) }">
      {{ item.name }}
    </span>
    <span v-if="meta || item.grade" class="meta">
      {{ meta || item.grade }}
    </span>
  </div>
</template>

<style scoped>
.entity-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.entity-row:hover {
  background: rgba(255, 255, 255, 0.08);
}

.entity-row.compact {
  padding: 4px 8px;
  font-size: 12px;
}

.meta {
  font-size: 11px;
  color: #888;
}
</style>

