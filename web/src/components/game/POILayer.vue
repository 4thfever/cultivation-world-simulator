<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { Rectangle } from 'pixi.js'
import { useMapStore } from '@/stores/map'
import { useTextures } from './composables/useTextures'

const TILE_SIZE = 64
// Avatars render at roughly 4.2 tiles. Keep graves prominent but slightly smaller.
const ICON_SIZE = TILE_SIZE * 3.5

const mapStore = useMapStore()
const { ensurePoiTexture, loadPoiTexture } = useTextures()

const visiblePois = computed(() => Array.from(mapStore.pois.values()))
const readyPoiIds = ref(new Set<string>())
const interactionHitArea = computed(() => new Rectangle(-ICON_SIZE / 2, -ICON_SIZE / 2, ICON_SIZE, ICON_SIZE))

onMounted(() => {
  // A page can preload the static map before a later death creates a POI.
  // Reconcile the dynamic POI snapshot when its render layer becomes active.
  void mapStore.refreshPois()
})

watch(
  visiblePois,
  async (pois) => {
    const expectedIds = new Set(pois.map((poi) => poi.id))
    await Promise.all(pois.map((poi) => loadPoiTexture(poi.icon_key ?? '')))
    readyPoiIds.value = expectedIds
  },
  { immediate: true },
)

const emit = defineEmits<{
  (e: 'poiSelected', payload: { type: 'avatar' | 'poi'; id: string; kind?: string; name?: string }): void
}>()

function handlePoiSelect(poi: { id: string; kind: string; name: string; deceased_avatar_id?: string }) {
  const deceasedAvatarId = poi.deceased_avatar_id || (
    poi.kind === 'grave' ? poi.id.split(':')[1] : undefined
  )

  if (poi.kind === 'grave' && deceasedAvatarId) {
    emit('poiSelected', {
      type: 'avatar',
      id: deceasedAvatarId,
      name: poi.name,
    })
    return
  }

  emit('poiSelected', {
    type: 'poi',
    id: poi.id,
    kind: poi.kind,
    name: poi.name,
  })
}
</script>

<template>
  <container :z-index="400">
    <!-- @vue-ignore -->
    <container
      v-for="poi in visiblePois"
      :key="poi.id"
      :x="poi.x * TILE_SIZE + TILE_SIZE / 2"
      :y="poi.y * TILE_SIZE + TILE_SIZE / 2"
      :hitArea="interactionHitArea"
      event-mode="static"
      cursor="pointer"
      @pointertap="handlePoiSelect(poi)"
    >
      <sprite
        v-if="readyPoiIds.has(poi.id) && ensurePoiTexture(poi.icon_key)"
        :texture="ensurePoiTexture(poi.icon_key)"
        :width="ICON_SIZE"
        :height="ICON_SIZE"
        :anchor="0.5"
        event-mode="none"
      />
    </container>
  </container>
</template>
