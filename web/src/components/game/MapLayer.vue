<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { Container, Sprite } from 'pixi.js'
import { useTextures } from './composables/useTextures'
import { useMapData } from '../../composables/useMapData'
import type { Region } from '../../types/game'

const TILE_SIZE = 64
const mapContainer = ref<Container>()
const { textures, isLoaded, loadSectTexture } = useTextures()
const { mapTiles, regions, isMapLoaded, loadMapData } = useMapData()
const regionStyleCache = new Map<string, Record<string, unknown>>()

const emit = defineEmits<{
  (e: 'mapLoaded', payload: { width: number, height: number }): void
  (e: 'regionSelected', payload: { type: 'region'; id: string; name?: string }): void
}>()

onMounted(() => {
  loadMapData().catch((error) => console.error('Map load error', error))
  if (isLoaded.value && isMapLoaded.value) {
    renderMap()
  }
})

watch(
  () => [isLoaded.value, isMapLoaded.value],
  ([texturesReady, mapReady]) => {
    if (texturesReady && mapReady) {
      renderMap()
    }
  }
)

async function renderMap() {
  if (!mapContainer.value || !mapTiles.value.length) return

  await preloadSectTextures(regions.value)
  mapContainer.value.removeChildren()

  const rows = mapTiles.value.length
  const cols = mapTiles.value[0]?.length ?? 0

  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const type = mapTiles.value[y][x]
      if (type === 'PLACEHOLDER') continue

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

      if (['SECT', 'CITY', 'CAVE', 'RUINS'].includes(type)) {
        sprite.width = TILE_SIZE * 2
        sprite.height = TILE_SIZE * 2
      } else {
        sprite.width = TILE_SIZE
        sprite.height = TILE_SIZE
      }

      sprite.eventMode = 'none'
      mapContainer.value.addChild(sprite)
    }
  }

  emit('mapLoaded', {
    width: cols * TILE_SIZE,
    height: rows * TILE_SIZE
  })
}

async function preloadSectTextures(regionList: Region[]) {
  const sectNames = Array.from(
    new Set(
      regionList
        .filter(region => region.type === 'sect' && region.sect_name)
        .map(region => region.sect_name as string)
    )
  )
  await Promise.all(sectNames.map(name => loadSectTexture(name)))
}

function resolveSectTexture(x: number, y: number) {
  const region = regions.value.find(r =>
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

function handleRegionSelect(region: Region) {
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
            v-for="r in regions"
            :key="r.name"
            :text="r.name"
            :x="r.x * TILE_SIZE + TILE_SIZE / 2"
            :y="r.y * TILE_SIZE + TILE_SIZE / 2"
            :anchor="0.5"
            :style="getRegionStyle(r.type)"
            event-mode="static"
            cursor="pointer"
            @pointertap="handleRegionSelect(r)"
        />
     </container>
  </container>
</template>
