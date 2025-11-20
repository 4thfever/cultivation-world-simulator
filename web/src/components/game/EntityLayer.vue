<script setup lang="ts">
import { useGameStore } from '../../stores/game'
import { useTextures } from './composables/useTextures'
import { computed } from 'vue'
import { Graphics } from 'pixi.js'

const store = useGameStore()
const { textures } = useTextures()
const TILE_SIZE = 64

function getTexture(avatar: any) {
  const key = `${(avatar.gender || 'male').toLowerCase()}_${avatar.pic_id || 1}`
  return textures.value[key]
}

function getScale(avatar: any) {
  const tex = getTexture(avatar)
  if (!tex) return 1
  return (TILE_SIZE * 1.8) / Math.max(tex.width, tex.height)
}

// Fallback graphics draw function
const drawFallback = (g: Graphics, avatar: any) => {
    g.clear()
    g.circle(0, 0, TILE_SIZE * 0.6)
    g.fill({ color: avatar.gender === 'female' ? 0xffaaaa : 0xaaaaff })
    g.stroke({ width: 2, color: 0x000000 })
}

const nameStyle = {
    fontFamily: '"Microsoft YaHei", sans-serif',
    fontSize: 24,
    fill: 0xffffff,
    stroke: { color: 0x000000, width: 4 },
    align: 'center'
}
</script>

<template>
  <container sortable-children>
    <container
      v-for="avatar in store.avatarList"
      :key="avatar.id"
      :x="avatar.x * TILE_SIZE + TILE_SIZE / 2"
      :y="avatar.y * TILE_SIZE + TILE_SIZE / 2"
      :z-index="avatar.y" 
    >
      <!-- Avatar Sprite -->
      <sprite
        v-if="getTexture(avatar)"
        :texture="getTexture(avatar)"
        :anchor-x="0.5"
        :anchor-y="0.8"
        :scale="getScale(avatar)"
      />
      
      <!-- Fallback Graphics -->
      <graphics
        v-else
        @render="g => drawFallback(g, avatar)"
      />

      <!-- Name Tag -->
      <text
        :text="avatar.name"
        :style="nameStyle"
        :anchor-x="0.5"
        :anchor-y="1"
        :y="-TILE_SIZE * 0.8"
      />
    </container>
  </container>
</template>

