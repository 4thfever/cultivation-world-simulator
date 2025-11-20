<script setup lang="ts">
import { useGameStore } from '../../stores/game'
import AnimatedAvatar from './AnimatedAvatar.vue'

const store = useGameStore()
const TILE_SIZE = 64
</script>

<template>
  <container sortable-children>
    <AnimatedAvatar
      v-for="avatar in store.avatarList"
      :key="avatar.id"
      :avatar="avatar"
      :tile-size="TILE_SIZE"
    />
  </container>
</template>
