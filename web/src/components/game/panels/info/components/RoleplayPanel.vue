<script setup lang="ts">
import { computed, onMounted, watch } from 'vue';

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

onMounted(() => {
  void refreshRoleplayState();
});
</script>

<template>
  <div class="roleplay-panel">
    <button
      v-if="!isCurrentAvatarControlled"
      class="roleplay-btn"
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
  border: 1px solid rgba(216, 186, 121, 0.28);
  background: linear-gradient(180deg, rgba(118, 84, 36, 0.48), rgba(71, 50, 19, 0.7));
  color: #f6ebcf;
  border-radius: 12px;
  padding: 10px 14px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
  text-align: center;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}

.roleplay-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(229, 201, 144, 0.42);
  background: linear-gradient(180deg, rgba(138, 99, 45, 0.58), rgba(81, 57, 23, 0.82));
}

.roleplay-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.roleplay-btn--secondary {
  border-color: rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
  color: #ccc;
}
</style>
