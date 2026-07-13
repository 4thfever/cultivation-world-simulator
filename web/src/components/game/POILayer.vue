<script setup lang="ts">
import { computed } from 'vue'
import { Rectangle } from 'pixi.js'
import { useMapStore } from '@/stores/map'
import { useTextures } from './composables/useTextures'

const TILE_SIZE = 64
const ICON_SIZE = 42

const mapStore = useMapStore()
const { ensurePoiTexture } = useTextures()

const visiblePois = computed(() => Array.from(mapStore.pois.values()))
const interactionHitArea = computed(() => new Rectangle(-ICON_SIZE / 2, -ICON_SIZE / 2, ICON_SIZE, ICON_SIZE))

const emit = defineEmits<{
  (e: 'poiSelected', payload: { type: 'poi'; id: string; kind: string; name?: string }): void
}>()

function handlePoiSelect(poi: { id: string; kind: string; name: string }) {
  emit('poiSelected', {
    type: 'poi',
    id: poi.id,
    kind: poi.kind,
    name: poi.name,
  })
}
</script>

<template>
  <container :z-index="180">
    <!-- @vue-ignore -->
    <container
      v-for="poi in visiblePois"
      :key="poi.id"
      :x="poi.x * TILE_SIZE + TILE_SIZE / 2"
      :y="poi.y * TILE_SIZE + TILE_SIZE / 2"
      :hitArea="interactionHitArea"
      event-mode="static"
      cursor="pointer"
      @pointertap="handlePoiSelect(poi)"
    >
      <sprite
        v-if="ensurePoiTexture(poi.icon_key)"
        :texture="ensurePoiTexture(poi.icon_key)"
        :width="ICON_SIZE"
        :height="ICON_SIZE"
        :anchor="0.5"
        event-mode="none"
      />
    </container>
  </container>
</template>
