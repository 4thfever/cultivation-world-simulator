import { defineStore } from 'pinia';
import { ref, shallowRef } from 'vue';
import type { MapMatrix, POISummary, RegionSummary } from '../types/core';
import type { MapRenderConfigDTO, POIUpdateDTO } from '../types/api';
import { worldApi } from '../api';
import { normalizeMapRenderConfig } from '../api/mappers/world';
import { logWarn } from '../utils/appError';

export const useMapStore = defineStore('map', () => {
  const mapData = shallowRef<MapMatrix>([]);
  const regions = shallowRef<Map<string | number, RegionSummary>>(new Map());
  const pois = shallowRef<Map<string, POISummary>>(new Map());
  const renderConfig = ref<MapRenderConfigDTO>(normalizeMapRenderConfig());
  const mapId = ref('classic');
  const mapName = ref('');
  const presetVersion = ref(1);
  const isLoaded = ref(false);
  let preloadMapPromise: Promise<void> | null = null;
  let preloadMapRequestId = 0;

  async function preloadMap() {
    if (isLoaded.value && mapData.value.length > 0) return;
    if (preloadMapPromise) return preloadMapPromise;

    const requestId = ++preloadMapRequestId;
    preloadMapPromise = (async () => {
      const mapRes = await worldApi.fetchMap();
      if (requestId !== preloadMapRequestId) return;

      mapData.value = mapRes.data;
      mapId.value = mapRes.mapId;
      mapName.value = mapRes.mapName;
      presetVersion.value = mapRes.presetVersion;
      renderConfig.value = normalizeMapRenderConfig(mapRes.renderConfig);
      const regionMap = new Map<string | number, RegionSummary>();
      mapRes.regions.forEach(r => regionMap.set(r.id, r));
      regions.value = regionMap;
      const poiMap = new Map<string, POISummary>();
      (mapRes.pois ?? []).forEach(p => poiMap.set(p.id, p));
      pois.value = poiMap;
      isLoaded.value = true;
    })()
      .catch((e) => {
        logWarn('MapStore preload map', e);
        throw e;
      })
      .finally(() => {
        if (requestId === preloadMapRequestId) {
          preloadMapPromise = null;
        }
      });

    return preloadMapPromise;
  }

  function reset() {
    preloadMapRequestId++;
    preloadMapPromise = null;
    mapData.value = [];
    regions.value = new Map();
    pois.value = new Map();
    renderConfig.value = normalizeMapRenderConfig();
    mapId.value = 'classic';
    mapName.value = '';
    presetVersion.value = 1;
    isLoaded.value = false;
  }

  function applyPoiUpdates(updates: POIUpdateDTO[] | undefined) {
    if (!Array.isArray(updates) || updates.length === 0) return;
    const next = new Map(pois.value);
    updates.forEach((update) => {
      if (update.op === 'remove') {
        next.delete(String(update.id));
      } else if (update.op === 'upsert' && update.poi) {
        next.set(String(update.poi.id), {
          ...update.poi,
          id: String(update.poi.id),
          icon_key: update.poi.icon_key ?? '',
          clickable: update.poi.clickable ?? true,
        });
      }
    });
    pois.value = next;
  }

  return {
    mapData,
    regions,
    pois,
    renderConfig,
    mapId,
    mapName,
    presetVersion,
    isLoaded,
    preloadMap,
    applyPoiUpdates,
    reset
  };
});
