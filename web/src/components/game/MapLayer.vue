<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { Container, Sprite, TilingSprite, Graphics, Ticker } from 'pixi.js'
import { useTextures } from './composables/useTextures'
import { useWorldStore } from '../../stores/world'
import { getRegionTextStyle } from '../../utils/mapStyles'
import { useAudio } from '../../composables/useAudio'
import type { RegionSummary } from '../../types/core'

const TILE_SIZE = 64
const mapContainer = ref<Container>()
const { textures, isLoaded, loadSectTexture, loadCityTexture, getTileTexture } = useTextures()
const worldStore = useWorldStore()

// 动态水面相关变量
let ticker: Ticker | null = null
let seaLayer: TilingSprite | null = null
let waterLayer: TilingSprite | null = null

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

onUnmounted(() => {
  cleanupTicker()
})

watch(
  () => [isLoaded.value, worldStore.isLoaded],
  ([texturesReady, mapReady]) => {
    if (texturesReady && mapReady) {
      renderMap()
    }
  }
)

function cleanupTicker() {
  if (ticker) {
    ticker.stop()
    ticker.destroy()
    ticker = null
  }
}

async function renderMap() {
  if (!mapContainer.value || !worldStore.mapData.length) return

  // 清理旧资源
  cleanupTicker()
  mapContainer.value.removeChildren()
  
  await preloadRegionTextures()

  if (!mapContainer.value) return // Check again after await
  const rows = worldStore.mapData.length
  const cols = worldStore.mapData[0]?.length ?? 0
  const mapWidth = cols * TILE_SIZE
  const mapHeight = rows * TILE_SIZE

  // --- 1. 准备动态水面层 (TilingSprite + Mask) ---
  
  // 创建海洋层 (底层水)
  const seaTex = textures.value['SEA_FULL'] || textures.value['SEA']
  
  // Pixi v8 style
  seaLayer = new TilingSprite({
    texture: seaTex,
    width: mapWidth,
    height: mapHeight
  })
  
  // 尝试缩小纹理比例，确保能看到花纹
  seaLayer.tileScale.set(0.5, 0.5) 
  
  const seaMask = new Graphics()
  seaLayer.mask = seaMask
  
  // 创建淡水层 (河流/湖泊)
  const waterTex = textures.value['WATER_FULL'] || textures.value['WATER']

  waterLayer = new TilingSprite({
    texture: waterTex,
    width: mapWidth,
    height: mapHeight
  })
  waterLayer.tileScale.set(0.5, 0.5)

  const waterMask = new Graphics()
  waterLayer.mask = waterMask

  // 容器用于存放普通地块（非水面）
  const groundContainer = new Container()

  // --- 2. 遍历地图数据 ---
  let hasSea = false
  let hasWater = false

  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const type = worldStore.mapData[y][x]

      // 处理特殊地块：海与水
      if (type === 'SEA') {
        seaMask.rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        seaMask.fill(0xffffff)
        hasSea = true
        continue
      }
      
      if (type === 'WATER') {
        waterMask.rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        waterMask.fill(0xffffff)
        hasWater = true
        continue
      }

      // 处理普通地块
      let tex = getTileTexture(type, x, y)

      // SECT 地块由 renderLargeRegions 渲染，这里跳过
      if (type === 'SECT') {
        continue
      }

      if (!tex) {
        throw new Error(`Missing texture for tile type: ${type} at (${x}, ${y})`)
      }

      if (!tex) continue

      const sprite = new Sprite(tex)
      sprite.x = x * TILE_SIZE
      sprite.y = y * TILE_SIZE
      sprite.roundPixels = true
      sprite.width = TILE_SIZE
      sprite.height = TILE_SIZE
      sprite.eventMode = 'none'
      
      groundContainer.addChild(sprite)
    }
  }

  // v8 不需要 endFill
  // seaMask.endFill()
  // waterMask.endFill()

  // --- 3. 组装图层 ---
  // 顺序：海 -> 水 -> 陆地
  if (hasSea && seaLayer) {
    mapContainer.value.addChild(seaLayer)
    // Mask 通常不需要 addChild，但如果 mask 行为异常，可以尝试 addChild 但设置 renderable = false
    // 在 v8 中通常不需要
    mapContainer.value.addChild(seaMask)
  }
  
  if (hasWater && waterLayer) {
    mapContainer.value.addChild(waterLayer)
    mapContainer.value.addChild(waterMask)
  }

  mapContainer.value.addChild(groundContainer)

  // --- 4. 启动动画 Ticker ---
  if (hasSea || hasWater) {
    ticker = new Ticker()
    ticker.add((tickerInstance: any) => {
      // v8: deltaMS / deltaTime
      let baseSpeed = 0.5
      
      const configSpeed = worldStore.frontendConfig?.water_speed || 'high' // default high as per old behavior
      if (configSpeed === 'none') {
        baseSpeed = 0
      } else if (configSpeed === 'low') {
        baseSpeed = 0.1
      } else if (configSpeed === 'medium') {
        baseSpeed = 0.3
      } else if (configSpeed === 'high') {
        baseSpeed = 0.8
      }

      if (baseSpeed === 0) return

      const speed = baseSpeed * tickerInstance.deltaTime
      
      if (hasSea && seaLayer) {
        // 海洋稍微向左下流动
        seaLayer.tilePosition.x -= speed * 0.5
        seaLayer.tilePosition.y += speed * 0.5
      }
      
      if (hasWater && waterLayer) {
        // 河流向右流动
        waterLayer.tilePosition.x += speed
        waterLayer.tilePosition.y += speed * 0.2
      }
    })
    ticker.start()
  }

  // 5. Render Large Regions (2x2) - 宗门、城市等覆盖层
  renderLargeRegions()

  emit('mapLoaded', {
    width: mapWidth,
    height: mapHeight
  })
}

async function preloadRegionTextures() {
  const regions = Array.from(worldStore.regions.values());
  
  // Sects - use sect_id instead of sect_name
  const sectIds = Array.from(
    new Set(
      regions
        .filter(region => region.type === 'sect' && region.sect_id)
        .map(region => region.sect_id as number)
    )
  )
  
  // Cities - use city id (convert to number)
  const cityIds = Array.from(
    new Set(
      regions
        .filter(region => region.type === 'city' && region.id)
        .map(region => {
          const id = typeof region.id === 'string' ? parseInt(region.id) : region.id
          return isNaN(id) ? null : id
        })
        .filter(id => id !== null)
    )
  ) as number[]

  await Promise.all([
      ...sectIds.map(id => loadSectTexture(id)),
      ...cityIds.map(id => loadCityTexture(id))
  ])
}

function renderLargeRegions() {
    const regions = Array.from(worldStore.regions.values());
    for (const region of regions) {
        let baseName: string | null = null;
        
        if (region.type === 'city' && region.id) {
            // Use city_id instead of city_name (convert to number)
            const cityId = typeof region.id === 'string' ? parseInt(region.id) : region.id
            if (!isNaN(cityId)) {
                baseName = `city_${cityId}`
            }
        } else if (region.type === 'sect' && region.sect_id) {
            // Use sect_id instead of sect_name
            baseName = `sect_${region.sect_id}`
        } else if (region.type === 'cultivate' && region.sub_type) {
            // Use sub_type from backend instead of name matching
            baseName = region.sub_type  // "cave" or "ruin"
        }

        if (baseName && mapContainer.value) {
            // Render 4 slices as 2x2 grid
            // Slice indices: 0=TL, 1=TR, 2=BL, 3=BR
            const positions = [
                { dx: 0, dy: 0, idx: 0 },  // TL
                { dx: 1, dy: 0, idx: 1 },  // TR
                { dx: 0, dy: 1, idx: 2 },  // BL
                { dx: 1, dy: 1, idx: 3 },  // BR
            ]
            
            for (const pos of positions) {
                const sliceKey = `${baseName}_${pos.idx}`
                const tex = textures.value[sliceKey]
                if (tex) {
                    const sprite = new Sprite(tex)
                    sprite.x = (region.x + pos.dx) * TILE_SIZE
                    sprite.y = (region.y + pos.dy) * TILE_SIZE
                    sprite.width = TILE_SIZE
                    sprite.height = TILE_SIZE
                    sprite.roundPixels = true
                    sprite.eventMode = 'none'
                    mapContainer.value.addChild(sprite)
                }
            }
        }
    }
}

function handleRegionSelect(region: RegionSummary) {
  useAudio().play('select')
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
            :style="getRegionTextStyle(r.type)"
            event-mode="static"
            cursor="pointer"
            @pointertap="handleRegionSelect(r)"
        />
     </container>
  </container>
</template>
