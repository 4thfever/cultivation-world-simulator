<script setup lang="ts">
import { useMapLayerRenderer } from './composables/useMapLayerRenderer'

const emit = defineEmits<{
  (e: 'mapLoaded', payload: { width: number, height: number }): void
  (e: 'regionSelected', payload: { type: 'region'; id: string; name?: string }): void
}>()

const {
  mapContainer,
  locale,
  visibleRegionLabels,
  getRegionTextStyle,
  handleRegionSelect,
} = useMapLayerRenderer(emit)
</script>

<template>
  <container>
     <!-- Tile Layer -->
     <container ref="mapContainer" />
     
     <!-- Region Labels Layer (Above tiles) -->
     <container :z-index="200">
        <!-- @vue-ignore -->
        <text
            v-for="r in visibleRegionLabels"
            :key="r.id"
            :text="r.displayName"
            :x="r.labelX"
            :y="r.labelY"
            :anchor="0.5"
            :style="getRegionTextStyle(r.type, locale)"
            event-mode="static"
            cursor="pointer"
            @pointertap="handleRegionSelect(r)"
        />
     </container>
  </container>
</template>
