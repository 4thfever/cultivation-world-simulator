<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { Container, Sprite } from 'pixi.js'
import { useTextures } from './composables/useTextures'
import { useWorldStore } from '../../stores/world'
import type { RegionSummary } from '../../types/core'

const TILE_SIZE = 64
const mapContainer = ref<Container>()
const { textures, isLoaded, loadSectTexture } = useTextures()
const worldStore = useWorldStore()
const regionStyleCache = new Map<string, Record<string, unknown>>()

const emit = defineEmits<{
  (e: 'mapLoaded', payload: { width: number, height: number }): void
  (e: 'regionSelected', payload: { type: 'region'; id: string; name?: string }): void
}>()

onMounted(() => {
  // Map data is loaded by worldStore.initialize() in App.vue or similar
  if (isLoaded.value && worldStore.isLoaded) {
    renderMap()
  }
})

watch(
  () => [isLoaded.value, worldStore.isLoaded],
  ([texturesReady, mapReady]) => {
    if (texturesReady && mapReady) {
      renderMap()
    }
  }
)

async function renderMap() {
  if (!mapContainer.value || !worldStore.mapData.length) return

  await preloadSectTextures()
  mapContainer.value.removeChildren()

  const rows = worldStore.mapData.length
  const cols = worldStore.mapData[0]?.length ?? 0

  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const type = worldStore.mapData[y][x]

      let tex = textures.value[type]

      if (type === 'SECT') {
        tex = resolveSectTexture(x, y) ?? textures.value['CITY']
      }

      if (!tex) {
        tex = textures.value['PLAIN']
      }

      if (!tex) continue

      const sprite = new Sprite(tex)
      sprite.x = x * TILE_SIZE
      sprite.y = y * TILE_SIZE
      // 开启像素取整，消除 Tile 之间的黑边缝隙
      sprite.roundPixels = true

      sprite.width = TILE_SIZE
      sprite.height = TILE_SIZE

      sprite.eventMode = 'none'
      mapContainer.value.addChild(sprite)
    }
  }

  emit('mapLoaded', {
    width: cols * TILE_SIZE,
    height: rows * TILE_SIZE
  })
}

async function preloadSectTextures() {
  const regions = Array.from(worldStore.regions.values());
  const sectNames = Array.from(
    new Set(
      regions
        .filter(region => region.type === 'sect' && region.sect_name)
        .map(region => region.sect_name as string)
    )
  )
  await Promise.all(sectNames.map(name => loadSectTexture(name)))
}

function resolveSectTexture(x: number, y: number) {
  const regions = Array.from(worldStore.regions.values());
  const region = regions.find(r =>
    r.type === 'sect' && Math.abs(r.x - x) < 3 && Math.abs(r.y - y) < 3
  )
  if (region?.sect_name) {
    const key = `SECT_${region.sect_name}`
    return textures.value[key] ?? null
  }
  return null
}

function getRegionStyle(type: string) {
  if (regionStyleCache.has(type)) {
    return regionStyleCache.get(type)
  }
  const style = {
    fontFamily: '"Microsoft YaHei", sans-serif',
    fontSize: type === 'sect' ? 48 : 64,
    fill: type === 'sect' ? '#ffcc00' : (type === 'city' ? '#ccffcc' : '#ffffff'),
    stroke: { color: '#000000', width: 8, join: 'round' },
    align: 'center',
    dropShadow: {
      color: '#000000',
      blur: 4,
      angle: Math.PI / 6,
      distance: 4,
      alpha: 0.8
    }
  }
  regionStyleCache.set(type, style)
  return style
}

function handleRegionSelect(region: RegionSummary) {
  emit('regionSelected', {
    type: 'region',
    id: String(region.id),
    name: region.name
  })
}
</script>

<template>
  <container>
     <!-- Tile Layer -->
     <container ref="mapContainer" />
     
     <!-- Region Labels Layer (Above tiles) -->
     <container :z-index="200">
        <!-- @vue-ignore -->
        <text
            v-for="r in Array.from(worldStore.regions.values())"
            :key="r.name"
            :text="r.name"
            :x="r.x * TILE_SIZE + TILE_SIZE / 2"
            :y="r.y * TILE_SIZE + TILE_SIZE * 1.5"
            :anchor="0.5"
            :style="getRegionStyle(r.type)"
            event-mode="static"
            cursor="pointer"
            @pointertap="handleRegionSelect(r)"
        />
     </container>
  </container>
</template>
