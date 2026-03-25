<script setup lang="ts">
defineProps<{
  name: string;
  meta?: string;
  metaLines?: string[];
  sub?: string;
  type?: string;
}>();

defineEmits(['click']);
</script>

<template>
  <div class="relation-row" @click="$emit('click')" v-sound>
    <div class="rel-head">
      <span class="rel-name">{{ name }}</span>
      <div v-if="metaLines?.length" class="rel-meta-stack">
        <span v-for="line in metaLines" :key="line" class="rel-type">{{ line }}</span>
      </div>
      <span v-else-if="meta" class="rel-type">{{ meta }}</span>
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
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 2px;
}

.rel-name {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: #eee;
  font-weight: bold;
}

.rel-meta-stack {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.rel-type {
  font-size: 12px;
  color: #aaa;
  line-height: 1.2;
  text-align: right;
}

.rel-sub {
  font-size: 11px;
  color: #666;
}
</style>
