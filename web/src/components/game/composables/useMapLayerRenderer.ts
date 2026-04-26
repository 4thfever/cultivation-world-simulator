import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { Container, Graphics, Sprite, Ticker, TilingSprite } from 'pixi.js'
import { useI18n } from 'vue-i18n'
import { useTextures } from './useTextures'
import { useMapStore } from '@/stores/map'
import { useAudio } from '@/composables/useAudio'
import type { RegionSummary } from '@/types/core'
import { getRegionTextStyle } from '@/utils/mapStyles'
import { buildVisibleRegionLabels } from '../utils/mapLabels'

const TILE_SIZE = 64

export function useMapLayerRenderer(emit: {
  (e: 'mapLoaded', payload: { width: number; height: number }): void
  (e: 'regionSelected', payload: { type: 'region'; id: string; name?: string }): void
}) {
  const mapContainer = ref<Container>()
  const {
    textures,
    isLoaded,
    preloadRegionTextures,
    getTileTexture,
  } = useTextures()
  const mapStore = useMapStore()
  const { locale } = useI18n()
  const { play } = useAudio()

  let ticker: Ticker | null = null
  let seaLayer: TilingSprite | null = null
  let waterLayer: TilingSprite | null = null

  const visibleRegionLabels = computed(() =>
    buildVisibleRegionLabels(Array.from(mapStore.regions.values()), locale.value),
  )

  function cleanupTicker() {
    if (ticker) {
      ticker.stop()
      ticker.destroy()
      ticker = null
    }
  }

  function getWaterSpeed() {
    const configSpeed = mapStore.renderConfig?.water_speed || 'high'
    if (configSpeed === 'none') return 0
    if (configSpeed === 'low') return 0.1
    if (configSpeed === 'medium') return 0.3
    return 0.8
  }

  function startWaterTicker(hasSea: boolean, hasWater: boolean) {
    if (!hasSea && !hasWater) return

    ticker = new Ticker()
    ticker.add((tickerInstance: Ticker) => {
      const baseSpeed = getWaterSpeed()
      if (baseSpeed === 0) return

      const speed = baseSpeed * tickerInstance.deltaTime
      if (hasSea && seaLayer) {
        seaLayer.tilePosition.x -= speed * 0.5
        seaLayer.tilePosition.y += speed * 0.5
      }
      if (hasWater && waterLayer) {
        waterLayer.tilePosition.x += speed
        waterLayer.tilePosition.y += speed * 0.2
      }
    })
    ticker.start()
  }

  function renderGroundAndWater(rows: number, cols: number, mapWidth: number, mapHeight: number) {
    const seaTex = textures.value.SEA_FULL || textures.value.SEA
    seaLayer = new TilingSprite({ texture: seaTex, width: mapWidth, height: mapHeight })
    seaLayer.tileScale.set(0.5, 0.5)
    const seaMask = new Graphics()
    seaLayer.mask = seaMask

    const waterTex = textures.value.WATER_FULL || textures.value.WATER
    waterLayer = new TilingSprite({ texture: waterTex, width: mapWidth, height: mapHeight })
    waterLayer.tileScale.set(0.5, 0.5)
    const waterMask = new Graphics()
    waterLayer.mask = waterMask

    const groundContainer = new Container()
    let hasSea = false
    let hasWater = false

    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const type = mapStore.mapData[y][x]
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
        if (type === 'SECT') continue

        const tex = getTileTexture(type, x, y)
        if (!tex) {
          throw new Error(`Missing texture for tile type: ${type} at (${x}, ${y})`)
        }

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

    if (hasSea && seaLayer) {
      mapContainer.value?.addChild(seaLayer)
      mapContainer.value?.addChild(seaMask)
    }
    if (hasWater && waterLayer) {
      mapContainer.value?.addChild(waterLayer)
      mapContainer.value?.addChild(waterMask)
    }
    mapContainer.value?.addChild(groundContainer)
    startWaterTicker(hasSea, hasWater)
  }

  function getLargeRegionBaseName(region: RegionSummary) {
    if (region.type === 'city' && region.id) {
      const cityId = typeof region.id === 'string' ? parseInt(region.id) : region.id
      return !Number.isNaN(cityId) ? `city_${cityId}` : null
    }
    if (region.type === 'sect' && region.sect_id) {
      return `sect_${region.sect_id}`
    }
    if (region.type === 'cultivate' && region.sub_type) {
      return region.sub_type
    }
    return null
  }

  function renderLargeRegions() {
    for (const region of mapStore.regions.values()) {
      const baseName = getLargeRegionBaseName(region)
      if (!baseName || !mapContainer.value) continue

      const positions = [
        { dx: 0, dy: 0, idx: 0 },
        { dx: 1, dy: 0, idx: 1 },
        { dx: 0, dy: 1, idx: 2 },
        { dx: 1, dy: 1, idx: 3 },
      ]

      for (const pos of positions) {
        const tex = textures.value[`${baseName}_${pos.idx}`]
        if (!tex) continue

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

  async function renderMap() {
    if (!mapContainer.value || !mapStore.mapData.length) return

    cleanupTicker()
    mapContainer.value.removeChildren()
    await preloadRegionTextures(mapStore.regions.values())

    if (!mapContainer.value) return
    const rows = mapStore.mapData.length
    const cols = mapStore.mapData[0]?.length ?? 0
    const mapWidth = cols * TILE_SIZE
    const mapHeight = rows * TILE_SIZE

    renderGroundAndWater(rows, cols, mapWidth, mapHeight)
    renderLargeRegions()
    emit('mapLoaded', { width: mapWidth, height: mapHeight })
  }

  function handleRegionSelect(region: RegionSummary) {
    play('select')
    emit('regionSelected', {
      type: 'region',
      id: String(region.id),
      name: region.name,
    })
  }

  onMounted(() => {
    if (isLoaded.value && mapStore.isLoaded) {
      void renderMap()
    }
  })

  onUnmounted(cleanupTicker)

  watch(
    () => [isLoaded.value, mapStore.isLoaded],
    ([texturesReady, mapReady]) => {
      if (texturesReady && mapReady) {
        void renderMap()
      }
    },
  )

  return {
    mapContainer,
    locale,
    visibleRegionLabels,
    getRegionTextStyle,
    handleRegionSelect,
  }
}
