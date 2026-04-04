<script setup lang="ts">
import GameStartPanel from '@/components/game/panels/system/GameStartPanel.vue'

defineProps<{
  gameInitialized: boolean
}>()
</script>

<template>
  <GameStartPanel :readonly="gameInitialized" />
</template>
