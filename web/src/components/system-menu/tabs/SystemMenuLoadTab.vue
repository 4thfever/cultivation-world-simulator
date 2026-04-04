<script setup lang="ts">
import SaveLoadPanel from '@/components/game/panels/system/SaveLoadPanel.vue'

const emit = defineEmits<{
  (e: 'close'): void
}>()
</script>

<template>
  <SaveLoadPanel mode="load" @close="emit('close')" />
</template>
