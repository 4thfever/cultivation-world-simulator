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

  async function preloadMap() {
    try {
      const mapRes = await worldApi.fetchMap();
      mapData.value = mapRes.data;
      renderConfig.value = normalizeMapRenderConfig(mapRes.renderConfig);
      const regionMap = new Map<string | number, RegionSummary>();
      mapRes.regions.forEach(r => regionMap.set(r.id, r));
      regions.value = regionMap;
      isLoaded.value = true;
    } catch (e) {
      logWarn('MapStore preload map', e);
      throw e;
    }
  }

  function reset() {
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
