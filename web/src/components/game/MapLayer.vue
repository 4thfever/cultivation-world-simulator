<script setup lang="ts">
import { ref, onMounted, watch, inject } from 'vue'
import { Container, Sprite } from 'pixi.js'
import { useTextures } from './composables/useTextures'

const mapContainer = ref<Container>()
const { textures, isLoaded, loadSectTexture } = useTextures()
const TILE_SIZE = 64
const regions = ref<any[]>([])

const emit = defineEmits(['mapLoaded'])

async function initMap() {
  if (!mapContainer.value || !isLoaded.value) return
  
  try {
    const res = await fetch('/api/map')
    const data = await res.json()
    const mapData = data.data
    regions.value = data.regions || []
    
    // 1. 预加载所有宗门的纹理
    const loadPromises: Promise<void>[] = []
    for (const r of regions.value) {
        if (r.type === 'sect' && r.sect_name) {
             // 使用 sect_name（宗门名）而不是 name（总部名）来加载图片
             loadPromises.push(loadSectTexture(r.sect_name))
        }
    }
    await Promise.all(loadPromises)
    
    if (!mapData) return

    // Imperative Tile Rendering
    mapContainer.value.removeChildren()
    
    const rows = mapData.length
    const cols = mapData[0].length
    
    console.log(`Rendering Map: ${cols}x${rows}`)
    
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const type = mapData[y][x]
        
        // 占位符直接跳过，不渲染任何东西（让背景透出来，或者就空着）
        if (type === 'PLACEHOLDER') continue

        let tex = textures.value[type] 
        
        // 特殊处理 SECT 类型
        if (type === 'SECT') {
             const r = regions.value.find(r => 
                r.type === 'sect' && Math.abs(r.x - x) < 3 && Math.abs(r.y - y) < 3
             )
             
             if (r && r.sect_name) {
                 // 使用 sect_name（宗门名）而不是 name（总部名）来匹配图片
                 const sectKey = `SECT_${r.sect_name}`
                 if (textures.value[sectKey]) {
                     tex = textures.value[sectKey]
                 } else {
                     tex = textures.value['CITY'] 
                 }
             } else {
                 tex = textures.value['CITY']
             }
        }
        
        if (!tex) tex = textures.value['PLAIN']
        
        if (tex) {
          const s = new Sprite(tex)
          s.x = x * TILE_SIZE
          s.y = y * TILE_SIZE
          
          // 2x2 大地块渲染逻辑
          if (['SECT', 'CITY', 'CAVE', 'RUINS'].includes(type)) {
              s.width = TILE_SIZE * 2
              s.height = TILE_SIZE * 2
              // 确保层级正确，大建筑可以稍微调整 zIndex 如果有深度排序需求
              // 但在这里 tile 是平铺的，只要顺序对就行
          } else {
              s.width = TILE_SIZE
              s.height = TILE_SIZE
          }
          
          s.eventMode = 'none' 
          mapContainer.value.addChild(s)
        }
      }
    }
    
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
