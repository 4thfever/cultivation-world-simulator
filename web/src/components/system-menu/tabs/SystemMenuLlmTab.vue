<script setup lang="ts">
import LLMConfigPanel from '@/components/game/panels/system/LLMConfigPanel.vue'

const emit = defineEmits<{
  (e: 'llm-ready'): void
}>()
</script>

<template>
  <LLMConfigPanel @config-saved="emit('llm-ready')" />
</template>
