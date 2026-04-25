import { defineStore } from 'pinia';
import { ref, shallowRef } from 'vue';
import type { MapMatrix, RegionSummary } from '../types/core';
import type { MapRenderConfigDTO } from '../types/api';
import { worldApi } from '../api';
import { normalizeMapRenderConfig } from '../api/mappers/world';
import { logWarn } from '../utils/appError';

export const useMapStore = defineStore('map', () => {
  const mapData = shallowRef<MapMatrix>([]);
  const regions = shallowRef<Map<string | number, RegionSummary>>(new Map());
  const renderConfig = ref<MapRenderConfigDTO>(normalizeMapRenderConfig());
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
      renderConfig.value = normalizeMapRenderConfig(mapRes.renderConfig);
      const regionMap = new Map<string | number, RegionSummary>();
      mapRes.regions.forEach(r => regionMap.set(r.id, r));
      regions.value = regionMap;
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
    renderConfig.value = normalizeMapRenderConfig();
    isLoaded.value = false;
  }

  return {
    mapData,
    regions,
    renderConfig,
    isLoaded,
    preloadMap,
    reset
  };
});
