<script setup lang="ts">
import { useGameStore } from '../../stores/game'
import AnimatedAvatar from './AnimatedAvatar.vue'

const store = useGameStore()
const TILE_SIZE = 64

const emit = defineEmits<{
  (e: 'avatarSelected', payload: { type: 'avatar'; id: string; name?: string }): void
}>()

function handleAvatarSelect(payload: { type: 'avatar'; id: string; name?: string }) {
  emit('avatarSelected', payload)
}
</script>

<template>
  <container sortable-children>
    <AnimatedAvatar
      v-for="avatar in store.avatarList"
      :key="avatar.id"
      :avatar="avatar"
      :tile-size="TILE_SIZE"
      @select="handleAvatarSelect"
    />
  </container>
</template>
