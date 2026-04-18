<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="roleplay-dock__idle">
    {{ t('game.roleplay.idle.hint') }}
  </div>
</template>

<style scoped>
.roleplay-dock__idle {
  font-size: 12px;
  line-height: 1.5;
  color: #cfc3a9;
}
</style>
