<script setup lang="ts">
import { Application } from 'vue3-pixi'
import { ref, onMounted } from 'vue'
import { useElementSize } from '@vueuse/core'
import { useGameStore } from '../../stores/game' // 引入 store
import Viewport from './Viewport.vue'
import MapLayer from './MapLayer.vue'
import EntityLayer from './EntityLayer.vue'
import { useTextures } from './composables/useTextures'

const container = ref<HTMLElement>()
const { width, height } = useElementSize(container)
const { loadBaseTextures, isLoaded } = useTextures()

const store = useGameStore() // 使用 store

const mapSize = ref({ width: 2000, height: 2000 })

const emit = defineEmits<{
  (e: 'avatarSelected', payload: { type: 'avatar'; id: string; name?: string }): void
  (e: 'regionSelected', payload: { type: 'region'; id: string; name?: string }): void
}>()

function onMapLoaded(size: { width: number, height: number }) {
    mapSize.value = size
}

function handleAvatarSelected(payload: { type: 'avatar'; id: string; name?: string }) {
  emit('avatarSelected', payload)
}

function handleRegionSelected(payload: { type: 'region'; id: string; name?: string }) {
  emit('regionSelected', payload)
}

const devicePixelRatio = window.devicePixelRatio || 1

onMounted(() => {
  loadBaseTextures()
})
</script>

<template>
  <div ref="container" class="game-canvas-container">
    <!-- 
      antialias: false (像素风必须关闭)
      resolution: devicePixelRatio (保证清晰度)
      background-color: 0x000000
    -->
    <Application
      v-if="width > 0 && height > 0"
      :width="width"
      :height="height"
      :background-color="0x000000"
      :antialias="false"
      :resolution="devicePixelRatio"
    >
      <Viewport
        v-if="isLoaded"
        :screen-width="width"
        :screen-height="height"
        :world-width="mapSize.width"
        :world-height="mapSize.height"
      >
        <!-- 
          使用 store.worldVersion 作为 key 
          当读档时，MapLayer 会被重新创建，从而重新加载地图数据
          但 Application 和 WebGL 上下文保持不变，避免崩溃
        -->
        <MapLayer 
          :key="store.worldVersion" 
          @mapLoaded="onMapLoaded" 
          @regionSelected="handleRegionSelected" 
        />
        <EntityLayer @avatarSelected="handleAvatarSelected" />
      </Viewport>
    </Application>
  </div>
</template>

<style scoped>
.game-canvas-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #000;
}
</style>
