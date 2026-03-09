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

  const inRange = (ax: number, ay: number) => Math.abs(ax) + Math.abs(ay) <= radius
  const isBoundary = (dx: number, dy: number) =>
    !inRange(dx + 1, dy) || !inRange(dx - 1, dy) || !inRange(dx, dy + 1) || !inRange(dx, dy - 1)

  // 1. 填充势力范围（半透明）
  g.setStrokeStyle(0)
  for (let dx = -radius; dx <= radius; dx++) {
    for (let dy = -radius; dy <= radius; dy++) {
      if (inRange(dx, dy)) {
        const tileX = centerX + dx
        const tileY = centerY + dy
        g.rect(tileX * TILE_SIZE, tileY * TILE_SIZE, TILE_SIZE, TILE_SIZE)
          .fill({ color: colorNum, alpha: 0.7 })
      }
    }
  }

  // 2. 只在外圈格子的「外侧」画粗边框，用提亮版宗门色更显眼
  const BORDER_WIDTH = 8
  const borderColor = brightenColor(colorNum, 0.55)
  const strokeOpt = { width: BORDER_WIDTH, color: borderColor, alpha: 1 }
  for (let dx = -radius; dx <= radius; dx++) {
    for (let dy = -radius; dy <= radius; dy++) {
      if (!inRange(dx, dy) || !isBoundary(dx, dy)) continue
      const px = (centerX + dx) * TILE_SIZE
      const py = (centerY + dy) * TILE_SIZE
      const pr = px + TILE_SIZE
      const pb = py + TILE_SIZE
      // 仅在与「外部」相邻的那一侧画线
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
