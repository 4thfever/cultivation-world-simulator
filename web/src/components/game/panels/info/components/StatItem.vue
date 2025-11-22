<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  label: string;
  value: string | number;
  subValue?: string | number;
  onClick?: () => void;
  fullWidth?: boolean;
}>();

const isClickable = computed(() => !!props.onClick);
</script>

<template>
  <div 
    class="stat-item" 
    :class="{ 'clickable': isClickable, 'full': fullWidth }"
    @click="onClick"
  >
    <label>{{ label }}</label>
    <span>
      {{ value }}
      <small v-if="subValue" class="sub-value">({{ subValue }})</small>
    </span>
  </div>
</template>

<style scoped>
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  border-radius: 4px;
  padding: 4px;
  margin: -4px;
  border: 1px solid transparent;
}

.stat-item.full {
  grid-column: span 2;
}

.stat-item.clickable {
  cursor: pointer;
  transition: background 0.2s;
}

.stat-item.clickable:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.1);
}

label {
  font-size: 11px;
  color: #888;
}

span {
  font-size: 13px;
  color: #ddd;
  font-weight: 500;
}

.sub-value {
  color: #666;
  font-size: 11px;
  margin-left: 4px;
}
</style>

