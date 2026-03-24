<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { Container, Graphics } from 'pixi.js'
import { useMapStore } from '../../stores/map'
import { useWorldStore } from '../../stores/world'
import { useSectStore } from '../../stores/sect'

const props = defineProps<{
  width: number
  height: number
}>()

const TILE_SIZE = 64
const container = ref<Container>()
const mapStore = useMapStore()
const worldStore = useWorldStore()
let influenceGraphics: Graphics | null = null
const sectStore = useSectStore()

function hexToNumber(hex: string): number {
  if (!hex) return 0xffffff
  return parseInt(hex.replace(/^#/, ''), 16)
}

/** 向白色混合，得到提亮版颜色（用于边框更显眼），t 为向白比例 0~1 */
function brightenColor(colorNum: number, t: number): number {
  const r = (colorNum >> 16) & 0xff
  const g = (colorNum >> 8) & 0xff
  const b = colorNum & 0xff
  const r2 = Math.round(r + (255 - r) * t)
  const g2 = Math.round(g + (255 - g) * t)
  const b2 = Math.round(b + (255 - b) * t)
  return (r2 << 16) | (g2 << 8) | b2
}

function updateInfluence() {
  if (!influenceGraphics) return
  
  const g = influenceGraphics
  g.clear()

  if (!sectStore.activeTerritories.length) {
    return
  }

  for (const summary of sectStore.activeTerritories) {
    const colorNum = hexToNumber(summary.color)
    g.setStrokeStyle(0)
    for (const tile of summary.owned_tiles ?? []) {
      g.rect(tile.x * TILE_SIZE, tile.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        .fill({ color: colorNum, alpha: 0.38 })
    }

    const BORDER_WIDTH = 6
    const borderColor = brightenColor(colorNum, 0.92)
    const strokeOpt = { width: BORDER_WIDTH, color: borderColor, alpha: 1 }
    for (const edge of summary.boundary_edges ?? []) {
      const px = edge.x * TILE_SIZE
      const py = edge.y * TILE_SIZE
      const pr = px + TILE_SIZE
      const pb = py + TILE_SIZE
      if (edge.side === 'left') {
        g.moveTo(px, py).lineTo(px, pb).stroke(strokeOpt)
      } else if (edge.side === 'right') {
        g.moveTo(pr, py).lineTo(pr, pb).stroke(strokeOpt)
      } else if (edge.side === 'top') {
        g.moveTo(px, py).lineTo(pr, py).stroke(strokeOpt)
      } else if (edge.side === 'bottom') {
        g.moveTo(px, pb).lineTo(pr, pb).stroke(strokeOpt)
      }
    }
  }
}

onMounted(() => {
  if (container.value) {
    influenceGraphics = new Graphics()
    influenceGraphics.eventMode = 'none'
    container.value.addChild(influenceGraphics)
    updateInfluence()
  }

  if (mapStore.isLoaded) {
    void sectStore.refreshTerritories()
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
    sectStore.activeTerritories
  ],
  () => {
    updateInfluence()
  },
  { deep: true }
)

watch(
  () => [mapStore.isLoaded, worldStore.year, worldStore.month],
  ([mapLoaded]) => {
    if (!mapLoaded) {
      updateInfluence()
      return
    }

    if (!sectStore.isLoading) {
      void sectStore.refreshTerritories()
    }
  }
)
</script>

<template>
  <container ref="container" :z-index="150" event-mode="none" />
</template>
