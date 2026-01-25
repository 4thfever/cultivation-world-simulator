<script setup lang="ts">
import { Application } from 'vue3-pixi'
import { ref, onMounted, computed } from 'vue'
import { useElementSize, useWindowSize } from '@vueuse/core'
import Viewport from './Viewport.vue'
import MapLayer from './MapLayer.vue'
import EntityLayer from './EntityLayer.vue'
import CloudLayer from './CloudLayer.vue'
import { useTextures } from './composables/useTextures'

const container = ref<HTMLElement>()
const { width: containerWidth, height: containerHeight } = useElementSize(container)
// 使用窗口大小作为 canvas 的固定尺寸，这样拖动 sidebar 时地图不会被缩放。
const { width: windowWidth, height: windowHeight } = useWindowSize()
const width = computed(() => windowWidth.value)
const height = computed(() => windowHeight.value)
const { loadBaseTextures, isLoaded } = useTextures()

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

const devicePixelRatio = 1 // 强制为 1，避免像素风游戏在高分屏下的坐标和缩放问题

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
      :resizeTo="container"
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
          注意：之前使用的 store.worldVersion 已移除。
          如果需要重新渲染 MapLayer（例如读档后），
          现在依赖于 worldStore.initialize() 触发 mapData 变更，
          以及 MapLayer 内部对 worldStore.isLoaded 的监听。
          如果发现读档不刷新的问题，可以在 MapLayer 增加 key。
        -->
        <MapLayer 
          @mapLoaded="onMapLoaded" 
          @regionSelected="handleRegionSelected" 
        />
        <EntityLayer @avatarSelected="handleAvatarSelected" />
        <CloudLayer :width="mapSize.width" :height="mapSize.height" />
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

.game-canvas-container :deep(canvas) {
  display: block;
}
</style>
