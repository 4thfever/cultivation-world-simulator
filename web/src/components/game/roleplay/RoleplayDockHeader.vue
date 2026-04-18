<script setup lang="ts">
defineProps<{
  avatarName: string
  statusText: string
  requestSummary: string
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  exit: []
}>()
</script>

<template>
  <div class="roleplay-dock__toolbar">
    <div class="roleplay-dock__meta">
      <span class="roleplay-dock__avatar">{{ avatarName }}</span>
      <span class="roleplay-dock__status">{{ statusText }}</span>
      <span class="roleplay-dock__notice">{{ requestSummary }}</span>
    </div>
    <button
      class="roleplay-dock__exit"
      :disabled="isSubmitting"
      @click="emit('exit')"
    >
      退出扮演
    </button>
  </div>
</template>

<style scoped>
.roleplay-dock__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 32px;
  padding: 6px 12px 5px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.roleplay-dock__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-size: 13px;
}

.roleplay-dock__avatar {
  font-size: 15px;
  font-weight: 700;
  color: #f4efe2;
  white-space: nowrap;
}

.roleplay-dock__status {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(110, 79, 29, 0.35);
  border: 1px solid rgba(212, 185, 133, 0.24);
  color: #dfcca4;
  font-size: 12px;
}

.roleplay-dock__notice {
  min-width: 0;
  color: #cfc3a9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.roleplay-dock__exit {
  border: 1px solid rgba(208, 180, 124, 0.26);
  border-radius: 8px;
  padding: 6px 10px;
  white-space: nowrap;
  font-size: 13px;
  color: #f6ecd2;
  background: rgba(86, 61, 23, 0.78);
  cursor: pointer;
}

.roleplay-dock__exit:disabled {
  cursor: default;
  opacity: 0.62;
}

@media (max-width: 900px) {
  .roleplay-dock__toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .roleplay-dock__meta {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
