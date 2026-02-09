<script setup lang="ts">
import { getEntityColor } from '@/utils/theme';
import type { EffectEntity } from '@/types/core';

defineProps<{
  tags: EffectEntity[];
}>();

defineEmits<{
  (e: 'click', item: EffectEntity): void;
}>();
</script>

<template>
  <div class="tags-container">
    <span 
      v-for="tag in tags" 
      :key="tag.id || tag.name" 
      class="tag"
      :style="{ borderColor: getEntityColor(tag) }"
      @click="$emit('click', tag)"
      v-sound
    >
      {{ tag.name }}
    </span>
  </div>
</template>

<style scoped>
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid #444;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  color: #ccc;
}

.tag:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: #666;
  color: #fff;
}
</style>

