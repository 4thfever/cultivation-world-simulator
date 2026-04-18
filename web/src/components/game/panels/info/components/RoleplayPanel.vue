<script setup lang="ts">
import { computed, watch } from 'vue';

import { useRoleplayStore } from '@/stores/roleplay';
import type { AvatarDetail } from '@/types/core';

const props = defineProps<{
  avatar: AvatarDetail;
}>();

const roleplayStore = useRoleplayStore();

const session = computed(() => roleplayStore.session);
const currentAvatarId = computed(() => props.avatar.id);
const controlledAvatarId = computed(() => session.value.controlled_avatar_id ?? '');
const isCurrentAvatarControlled = computed(() => controlledAvatarId.value === currentAvatarId.value);
const isAnotherAvatarControlled = computed(() => !!controlledAvatarId.value && !isCurrentAvatarControlled.value);

async function refreshRoleplayState() {
  await roleplayStore.fetchSession();
}

async function handleStartRoleplay() {
  await roleplayStore.startRoleplay(currentAvatarId.value);
}

async function handleStopRoleplay() {
  await roleplayStore.stopRoleplay(currentAvatarId.value);
}

watch(currentAvatarId, () => {
  void refreshRoleplayState();
}, { immediate: true });
</script>

<template>
  <div class="roleplay-panel">
    <button
      v-if="!isCurrentAvatarControlled"
      class="roleplay-btn roleplay-btn--primary"
      :disabled="isAnotherAvatarControlled || roleplayStore.isSubmitting"
      @click="handleStartRoleplay"
    >
      扮演
    </button>
    <button
      v-else
      class="roleplay-btn roleplay-btn--secondary"
      :disabled="roleplayStore.isSubmitting"
      @click="handleStopRoleplay"
    >
      退出扮演
    </button>
  </div>
</template>

<style scoped>
.roleplay-panel {
  display: flex;
  width: 100%;
}

.roleplay-btn {
  width: 100%;
  padding: 8px 14px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
  color: #ccc;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.2;
  text-align: center;
  transition: all 0.2s;
}

.roleplay-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
}

.roleplay-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.roleplay-btn--primary {
  background: linear-gradient(180deg, #2f8ef3 0%, #1d73cb 100%);
  color: #f8fbff;
  border-color: rgba(120, 190, 255, 0.4);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.14);
}

.roleplay-btn--primary:hover:not(:disabled) {
  background: linear-gradient(180deg, #44a1ff 0%, #2480de 100%);
}

.roleplay-btn--secondary {
  background: rgba(255, 255, 255, 0.06);
  color: #ddd6c8;
  border-color: rgba(255, 255, 255, 0.18);
}
</style>
