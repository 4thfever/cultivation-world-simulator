<script setup lang="ts">
import { computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { useRoleplayStore } from '@/stores/roleplay';
import { useUiStore } from '@/stores/ui';
import type { AvatarDetail } from '@/types/core';

const props = defineProps<{
  avatar: AvatarDetail;
}>();

const { t } = useI18n();
const roleplayStore = useRoleplayStore();
const uiStore = useUiStore();

const session = computed(() => roleplayStore.session);
const currentAvatarId = computed(() => props.avatar.id);
const controlledAvatarId = computed(() => session.value.controlled_avatar_id ?? '');
const isCurrentAvatarControlled = computed(() => controlledAvatarId.value === currentAvatarId.value);
const isAnotherAvatarControlled = computed(() => !!controlledAvatarId.value && !isCurrentAvatarControlled.value);
const controlledAvatarName = computed(() => {
  const context = session.value.last_prompt_context ?? {};
  const rawName = typeof context.avatar_name === 'string' ? context.avatar_name : '';
  return rawName || controlledAvatarId.value || t('game.roleplay.fallback.avatar_name');
});

async function refreshRoleplayState() {
  await roleplayStore.fetchSession();
}

async function handleStartRoleplay() {
  await roleplayStore.startRoleplay(currentAvatarId.value);
}

async function handleStopRoleplay() {
  await roleplayStore.stopRoleplay(currentAvatarId.value);
}

function handleGoToControlledAvatar() {
  if (controlledAvatarId.value) {
    uiStore.select('avatar', controlledAvatarId.value);
  }
}

watch(currentAvatarId, () => {
  void refreshRoleplayState();
}, { immediate: true });
</script>

<template>
  <div class="roleplay-panel">
    <div v-if="isAnotherAvatarControlled" class="roleplay-panel__busy">
      {{ t('game.roleplay.panel.controlled_by', { avatar: controlledAvatarName }) }}
    </div>
    <button
      v-if="!isCurrentAvatarControlled"
      class="roleplay-btn roleplay-btn--primary"
      :disabled="isAnotherAvatarControlled || roleplayStore.isSubmitting"
      @click="handleStartRoleplay"
    >
      {{ t('game.roleplay.panel.start') }}
    </button>
    <button
      v-if="isAnotherAvatarControlled"
      class="roleplay-btn roleplay-btn--ghost"
      :disabled="roleplayStore.isSubmitting"
      @click="handleGoToControlledAvatar"
    >
      {{ t('game.roleplay.panel.go_to_controlled') }}
    </button>
    <button
      v-else-if="isCurrentAvatarControlled"
      class="roleplay-btn roleplay-btn--secondary"
      :disabled="roleplayStore.isSubmitting"
      @click="handleStopRoleplay"
    >
      {{ t('game.roleplay.panel.stop') }}
    </button>
  </div>
</template>

<style scoped>
.roleplay-panel {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.roleplay-panel__busy {
  color: #b9b0a0;
  font-size: 12px;
  line-height: 1.45;
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

.roleplay-btn--ghost {
  background: transparent;
  color: #cfc6b7;
  border-color: rgba(255, 255, 255, 0.12);
}
</style>
