<script setup lang="ts">
import { Rectangle } from 'pixi.js'
import { useMapLayerRenderer } from './composables/useMapLayerRenderer'
import { estimateRegionLabelSize } from './utils/mapLabels'

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

function getRegionLabelHitArea(label: string, type: string, locale: string) {
  const { width, height } = estimateRegionLabelSize(label, type, locale)
  return new Rectangle(-width / 2, -height / 2, width, height)
}

</script>

<template>
  <container>
     <!-- Tile Layer -->
     <container ref="mapContainer" />
     
     <!-- Region Labels Layer (Above tiles) -->
     <container :z-index="200">
        <!-- @vue-ignore -->
        <container
            v-for="r in visibleRegionLabels"
            :key="r.id"
            :x="r.labelX"
            :y="r.labelY"
            :hitArea="getRegionLabelHitArea(r.displayName, r.type, locale)"
            event-mode="static"
            cursor="pointer"
            @pointertap="handleRegionSelect(r)"
        >
            <!-- @vue-ignore -->
            <text
                :text="r.displayName"
                :anchor="0.5"
                :style="getRegionTextStyle(r.type, locale)"
                event-mode="none"
            />
        </container>
     </container>
  </container>
</template>
