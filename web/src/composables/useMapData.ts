import { ref } from 'vue'
import type { MapMatrix, Region } from '../types/game'
import { gameApi } from '../services/gameApi'

const mapTiles = ref<MapMatrix>([])
const regions = ref<Region[]>([])
const isMapLoaded = ref(false)
let inFlight: Promise<void> | null = null

async function loadMapData() {
  if (isMapLoaded.value) return
  if (inFlight) return inFlight

  inFlight = gameApi.getMap()
    .then((data) => {
      mapTiles.value = data.data ?? []
      regions.value = data.regions ?? []
      isMapLoaded.value = mapTiles.value.length > 0
    })
    .finally(() => {
      inFlight = null
    })

  return inFlight
}

export function useMapData() {
  return {
    mapTiles,
    regions,
    isMapLoaded,
    loadMapData
  }
}

