<script setup lang="ts">
defineProps<{
  name: string;
  meta?: string;
  sub?: string;
  type?: string;
}>();

defineEmits(['click']);
</script>

<template>
  <div class="relation-row" @click="$emit('click')" v-sound>
    <div class="rel-head">
      <span class="rel-name">{{ name }}</span>
      <span v-if="meta" class="rel-type">{{ meta }}</span>
    </div>
    <div v-if="sub" class="rel-sub">{{ sub }}</div>
  </div>
</template>

<style scoped>
.relation-row {
  padding: 6px 8px;
  background: rgba(0, 0, 0, 0.2);
  border-left: 2px solid #333;
  cursor: pointer;
  transition: all 0.2s;
}

.relation-row:hover {
  background: rgba(255, 255, 255, 0.05);
  border-left-color: #666;
}

.rel-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2px;
}

.rel-name {
  font-size: 13px;
  color: #eee;
  font-weight: bold;
}

.rel-type {
  font-size: 12px;
  color: #aaa;
}

.rel-sub {
  font-size: 11px;
  color: #666;
}
</style>
