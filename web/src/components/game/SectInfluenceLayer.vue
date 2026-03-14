<script setup lang="ts">
import { onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import { Container, Graphics } from 'pixi.js'
import { useMapStore } from '../../stores/map'
import { useWorldStore } from '../../stores/world'
import { worldApi } from '../../api'
import type { SectTerritorySummaryDTO } from '../../types/api'
import { logWarn } from '../../utils/appError'

const props = defineProps<{
  width: number
  height: number
}>()

const TILE_SIZE = 64
const container = ref<Container>()
const mapStore = useMapStore()
const worldStore = useWorldStore()
const sectTerritories = shallowRef<SectTerritorySummaryDTO[]>([])

let influenceGraphics: Graphics | null = null
let territoryRequestId = 0

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

  if (!sectTerritories.value.length) {
    return
  }

  const regions = Array.from(mapStore.regions.values())
  for (const summary of sectTerritories.value) {
    if (!summary.is_active) continue

    const hqRegion = regions.find(
      (region) =>
        region.type === 'sect' &&
        region.sect_is_active !== false &&
        String(region.sect_id) === String(summary.id)
    )
    if (!hqRegion) continue

    const centerX = hqRegion.x
    const centerY = hqRegion.y
    const radius = summary.influence_radius
    if (radius < 0) continue

    const colorNum = hexToNumber(summary.color)
    const inRange = (ax: number, ay: number) => Math.abs(ax) + Math.abs(ay) <= radius
    const isBoundary = (dx: number, dy: number) =>
      !inRange(dx + 1, dy) || !inRange(dx - 1, dy) || !inRange(dx, dy + 1) || !inRange(dx, dy - 1)

    g.setStrokeStyle(0)
    for (let dx = -radius; dx <= radius; dx++) {
      for (let dy = -radius; dy <= radius; dy++) {
        if (inRange(dx, dy)) {
          const tileX = centerX + dx
          const tileY = centerY + dy
          g.rect(tileX * TILE_SIZE, tileY * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            .fill({ color: colorNum, alpha: 0.38 })
        }
      }
    }

    const BORDER_WIDTH = 6
    const borderColor = brightenColor(colorNum, 0.92)
    const strokeOpt = { width: BORDER_WIDTH, color: borderColor, alpha: 1 }
    for (let dx = -radius; dx <= radius; dx++) {
      for (let dy = -radius; dy <= radius; dy++) {
        if (!inRange(dx, dy) || !isBoundary(dx, dy)) continue
        const px = (centerX + dx) * TILE_SIZE
        const py = (centerY + dy) * TILE_SIZE
        const pr = px + TILE_SIZE
        const pb = py + TILE_SIZE
        if (!inRange(dx + 1, dy)) {
          g.moveTo(pr, py).lineTo(pr, pb).stroke(strokeOpt)
        }
        if (!inRange(dx - 1, dy)) {
          g.moveTo(px, py).lineTo(px, pb).stroke(strokeOpt)
        }
        if (!inRange(dx, dy + 1)) {
          g.moveTo(px, pb).lineTo(pr, pb).stroke(strokeOpt)
        }
        if (!inRange(dx, dy - 1)) {
          g.moveTo(px, py).lineTo(pr, py).stroke(strokeOpt)
        }
      }
    }
  }
}

async function refreshSectTerritories() {
  const currentRequestId = ++territoryRequestId

  try {
    const response = await worldApi.fetchSectTerritories()
    if (currentRequestId !== territoryRequestId) return
    sectTerritories.value = response.sects ?? []
    updateInfluence()
  } catch (error) {
    if (currentRequestId !== territoryRequestId) return
    logWarn('SectInfluenceLayer fetch sect territories', error)
    sectTerritories.value = []
    updateInfluence()
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
    void refreshSectTerritories()
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
    mapStore.regions,
    sectTerritories.value
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
      sectTerritories.value = []
      updateInfluence()
      return
    }

    void refreshSectTerritories()
  }
)
</script>

<template>
  <container ref="container" :z-index="150" event-mode="none" />
</template>
