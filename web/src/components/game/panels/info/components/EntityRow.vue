<script setup lang="ts">
import { getEntityColor } from '@/utils/theme';
import type { EffectEntity } from '@/types/core';

defineProps<{
  item: EffectEntity;
  meta?: string; // e.g. "熟练度 50%"
  compact?: boolean;
}>();

defineEmits(['click']);
</script>

<template>
  <div 
    class="entity-row" 
    :class="{ 'compact': compact }"
    @click="$emit('click')"
    v-sound
  >
    <span class="name" :style="{ color: getEntityColor(item) }">
      {{ item.name }}
    </span>
    <span class="info">
      <span v-if="meta" class="meta">{{ meta }}</span>
      <span v-if="item.grade" class="grade">{{ item.grade }}</span>
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

.info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.grade {
  font-size: 11px;
  padding: 1px 5px;
  background: rgba(255, 215, 0, 0.15);
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: 3px;
  color: #daa520;
}

.meta {
  font-size: 11px;
  color: #888;
}
</style>
