<script setup lang="ts">
defineProps<{
  title: string
  caption: string
}>()
</script>

<template>
  <div class="roleplay-dock__section-head">
    <span class="roleplay-dock__section-title">{{ title }}</span>
    <span class="roleplay-dock__section-caption">{{ caption }}</span>
  </div>
</template>

<style scoped>
.roleplay-dock__section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  padding-bottom: 5px;
  margin-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.roleplay-dock__section-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #d8ccb1;
}

.roleplay-dock__section-caption {
  font-size: 12px;
  color: #8f8776;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
