<script setup lang="ts">
import { Application } from 'vue3-pixi'
import { ref, onMounted } from 'vue'
import { useElementSize } from '@vueuse/core'
import Viewport from './Viewport.vue'
import MapLayer from './MapLayer.vue'
import EntityLayer from './EntityLayer.vue'
import { useTextures } from './composables/useTextures'

const container = ref<HTMLElement>()
const { width, height } = useElementSize(container)
const { loadBaseTextures, isLoaded } = useTextures()

const mapSize = ref({ width: 2000, height: 2000 })

function onMapLoaded(size: { width: number, height: number }) {
    mapSize.value = size
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
        <MapLayer @mapLoaded="onMapLoaded" />
        <EntityLayer />
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
