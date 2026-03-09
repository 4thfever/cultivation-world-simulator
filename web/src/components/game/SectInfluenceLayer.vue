<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { Container, Graphics } from 'pixi.js'
import { useUiStore } from '../../stores/ui'
import type { SectDetail } from '../../types/core'
import { useMapStore } from '../../stores/map'

const props = defineProps<{
  width: number
  height: number
}>()

const TILE_SIZE = 64
const container = ref<Container>()
const uiStore = useUiStore()
const mapStore = useMapStore()

let influenceGraphics: Graphics | null = null

function hexToNumber(hex: string): number {
  if (!hex) return 0xffffff
  return parseInt(hex.replace(/^#/, ''), 16)
}

function updateInfluence() {
  if (!influenceGraphics) return
  
  const g = influenceGraphics
  g.clear()
  
  const target = uiStore.selectedTarget
  const detail = uiStore.detailData as SectDetail | null
  
  if (!target || target.type !== 'sect' || !detail || detail.influence_radius === undefined) {
    return
  }

  // Find the region for this sect to get the central coordinates
  const regions = Array.from(mapStore.regions.values())
  // Use loose equality or string conversion since id from target could be string
  const hqRegion = regions.find(r => r.type === 'sect' && String(r.sect_id) === String(target.id))
  
  if (!hqRegion) return
  
  const centerX = hqRegion.x
  const centerY = hqRegion.y
  const radius = detail.influence_radius
  
  // Calculate color
  const colorNum = hexToNumber(detail.color)
  
  // PixiJS v8 fill API:
  g.setStrokeStyle(0)
  for (let dx = -radius; dx <= radius; dx++) {
    for (let dy = -radius; dy <= radius; dy++) {
      if (Math.abs(dx) + Math.abs(dy) <= radius) {
        const tileX = centerX + dx
        const tileY = centerY + dy
        g.rect(tileX * TILE_SIZE, tileY * TILE_SIZE, TILE_SIZE, TILE_SIZE)
      }
    }
  }
  g.fill({ color: colorNum, alpha: 0.3 })
}

onMounted(() => {
  if (container.value) {
    influenceGraphics = new Graphics()
    influenceGraphics.eventMode = 'none'
    container.value.addChild(influenceGraphics)
    updateInfluence()
  }
})

onUnmounted(() => {
  if (influenceGraphics) {
    influenceGraphics.destroy()
    influenceGraphics = null
  }
})

watch(
  () => [
    uiStore.selectedTarget, 
    uiStore.detailData
  ],
  () => {
    updateInfluence()
  },
  { deep: true }
)
</script>

<template>
  <container ref="container" :z-index="150" event-mode="none" />
</template>
