<script setup lang="ts">
import { computed, ref } from 'vue'
import { Graphics, type TextStyle } from 'pixi.js'
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

const hoveredRegionId = ref<string | null>(null)

function getRegionKey(region: { id: string | number }) {
  return String(region.id)
}

function handleRegionPointerOver(region: { id: string | number }) {
  hoveredRegionId.value = getRegionKey(region)
}

function handleRegionPointerOut(region: { id: string | number }) {
  if (hoveredRegionId.value === getRegionKey(region)) {
    hoveredRegionId.value = null
  }
}

function isRegionHovered(region: { id: string | number }) {
  return hoveredRegionId.value === getRegionKey(region)
}

function getHoverRegionTextStyle(type: string): TextStyle {
  const baseStyle = getRegionTextStyle(type, locale.value)
  return new TextStyle({
    ...baseStyle,
    stroke: { color: '#f6d68a', width: 5 },
    dropShadow: {
      color: '#000000',
      blur: 4,
      angle: Math.PI / 6,
      distance: 2,
      alpha: 0.9,
    },
  })
}

function getRegionLabelStyle(region: { id: string | number; type: string }) {
  return isRegionHovered(region)
    ? getHoverRegionTextStyle(region.type)
    : getRegionTextStyle(region.type, locale.value)
}

const hoverLabelBgAlpha = computed(() => hoveredRegionId.value ? 1 : 0)

function drawRegionLabelHoverBg(g: Graphics, width: number, height: number) {
  g.clear()
  const padX = 16
  const padY = 8
  const bgWidth = Math.max(width + padX * 2, 54)
  const bgHeight = Math.max(height + padY * 2, 30)
  g.roundRect(-bgWidth / 2, -bgHeight / 2, bgWidth, bgHeight, 8)
  g.fill({ color: 0x19150e, alpha: 0.78 })
  g.stroke({ width: 2, color: 0xf6d68a, alpha: 0.68 })
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
        >
            <graphics
                v-if="isRegionHovered(r)"
                event-mode="none"
                :alpha="hoverLabelBgAlpha"
                @effect="(g: Graphics) => drawRegionLabelHoverBg(g, Math.max(r.displayName.length * 18, 38), 24)"
            />
            <!-- @vue-ignore -->
            <text
                :text="r.displayName"
                :anchor="0.5"
                :style="getRegionLabelStyle(r)"
                :scale="isRegionHovered(r) ? 1.05 : 1"
                event-mode="static"
                cursor="pointer"
                @pointerenter="handleRegionPointerOver(r)"
                @pointerover="handleRegionPointerOver(r)"
                @pointermove="handleRegionPointerOver(r)"
                @mouseenter="handleRegionPointerOver(r)"
                @mouseover="handleRegionPointerOver(r)"
                @pointerleave="handleRegionPointerOut(r)"
                @pointerout="handleRegionPointerOut(r)"
                @mouseleave="handleRegionPointerOut(r)"
                @mouseout="handleRegionPointerOut(r)"
                @pointertap="handleRegionSelect(r)"
            />
        </container>
     </container>
  </container>
</template>
