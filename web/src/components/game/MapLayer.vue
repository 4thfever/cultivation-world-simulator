<script setup lang="ts">
import { ref, onMounted, watch, inject } from 'vue'
import { Container, Sprite } from 'pixi.js'
import { useTextures } from './composables/useTextures'

const mapContainer = ref<Container>()
const { textures, isLoaded } = useTextures()
const TILE_SIZE = 64
const regions = ref<any[]>([])

const emit = defineEmits(['mapLoaded'])

async function initMap() {
  if (!mapContainer.value || !isLoaded.value) return
  
  try {
    const res = await fetch('/api/map')
    const data = await res.json()
    const mapData = data.data
    // Regions are already provided by backend
    regions.value = data.regions || []
    
    if (!mapData) return

    // Imperative Tile Rendering
    mapContainer.value.removeChildren()
    
    const rows = mapData.length
    const cols = mapData[0].length
    
    console.log(`Rendering Map: ${cols}x${rows}`)
    
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const type = mapData[y][x]
        const tex = textures.value[type] || textures.value['PLAIN']
        
        if (tex) {
          const s = new Sprite(tex)
          s.x = x * TILE_SIZE
          s.y = y * TILE_SIZE
          s.width = TILE_SIZE
          s.height = TILE_SIZE
          // Optimization: Static tiles don't need interactivity
          s.eventMode = 'none' 
          mapContainer.value.addChild(s)
        }
      }
    }
    
    // Emit world size
    emit('mapLoaded', { 
        width: cols * TILE_SIZE, 
        height: rows * TILE_SIZE 
    })
    
  } catch (e) {
    console.error("Map load error", e)
  }
}

watch(isLoaded, (val) => {
  if (val) initMap()
})

onMounted(() => {
  if (isLoaded.value) initMap()
})

function getRegionStyle(type: string) {
    const base = {
        fontFamily: '"Microsoft YaHei", sans-serif',
        fontSize: type === 'sect' ? 48 : 64, 
        fill: type === 'sect' ? 0xffcc00 : (type === 'city' ? 0xccffcc : 0xffffff),
        stroke: { color: 0x000000, width: 8, join: 'round' }, 
        align: 'center',
        dropShadow: {
            color: '#000000',
            blur: 4,
            angle: Math.PI / 6,
            distance: 4,
            alpha: 0.8
        }
    }
    return base
}
</script>

<template>
  <container>
     <!-- Tile Layer -->
     <container ref="mapContainer" />
     
     <!-- Region Labels Layer (Above tiles) -->
     <container :z-index="200">
        <text
            v-for="r in regions"
            :key="r.name"
            :text="r.name"
            :x="r.x * TILE_SIZE + TILE_SIZE / 2"
            :y="r.y * TILE_SIZE + TILE_SIZE / 2"
            :anchor="0.5"
            :style="getRegionStyle(r.type)"
        />
     </container>
  </container>
</template>
