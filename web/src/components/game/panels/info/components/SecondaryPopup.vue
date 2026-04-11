<script setup lang="ts">
import type { EffectEntity } from '@/types/core';
import EntityDetailCard from './EntityDetailCard.vue';
import xIcon from '@/assets/icons/ui/lucide/x.svg';

const props = defineProps<{
  item: EffectEntity | null;
}>();

defineEmits(['close']);
</script>

<template>
  <Teleport to="body">
    <div v-if="item" class="secondary-panel">
      <div class="sec-header">
        <span class="sec-title">{{ item.name }}</span>
        <button class="close-btn" aria-label="Close" @click="$emit('close')">
          <span class="close-icon" :style="{ '--icon-url': `url(${xIcon})` }" aria-hidden="true"></span>
        </button>
      </div>
      
      <div class="sec-body">
        <EntityDetailCard :item="item" :show-name="false" />
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.secondary-panel {
  position: fixed;
  top: 96px;       /* 36px (StatusBar) + 60px (InfoPanel top offset) */
  right: calc(var(--cws-sidebar-width, 400px) + clamp(340px, 26vw, 376px) + 32px);
  width: 260px;
  background: rgba(32, 32, 32, 0.98);
  border: 1px solid #555;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.8);
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: min(260px, calc(100vw - var(--cws-sidebar-width, 400px) - clamp(340px, 26vw, 376px) - 56px));
}

.sec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #444;
  padding-bottom: 8px;
}

.sec-title {
  font-size: 15px;
  font-weight: bold;
  color: #eee;
}

.close-btn {
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 0 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #fff;
}

.close-icon {
  width: 18px;
  height: 18px;
  display: inline-block;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
}

.sec-body {
  display: block;
}
</style>
