import { defineStore } from 'pinia';
import { ref, shallowRef } from 'vue';
import type { MapMatrix, RegionSummary } from '../types/core';
import type { FrontendConfigDTO } from '../types/api';
import { worldApi } from '../api';
import { normalizeFrontendConfig } from '../api/mappers/world';
import { logWarn } from '../utils/appError';

export const useMapStore = defineStore('map', () => {
  const mapData = shallowRef<MapMatrix>([]);
  const regions = shallowRef<Map<string | number, RegionSummary>>(new Map());
  const frontendConfig = ref<FrontendConfigDTO>(normalizeFrontendConfig());
  const isLoaded = ref(false);

  async function preloadMap() {
    try {
      const mapRes = await worldApi.fetchMap();
      mapData.value = mapRes.data;
      frontendConfig.value = normalizeFrontendConfig(mapRes.config);
      const regionMap = new Map();
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
    frontendConfig.value = normalizeFrontendConfig();
    isLoaded.value = false;
  }

  return {
    mapData,
    regions,
    frontendConfig,
    isLoaded,
    preloadMap,
    reset
  };
});
