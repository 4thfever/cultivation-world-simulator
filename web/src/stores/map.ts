import { defineStore } from 'pinia';
import { ref, shallowRef } from 'vue';
import type { MapMatrix, RegionSummary } from '../types/core';
import { worldApi } from '../api';

export const useMapStore = defineStore('map', () => {
  const mapData = shallowRef<MapMatrix>([]);
  const regions = shallowRef<Map<string | number, RegionSummary>>(new Map());
  const frontendConfig = ref<Record<string, any>>({});
  const isLoaded = ref(false);

  async function preloadMap() {
    try {
      const mapRes = await worldApi.fetchMap();
      mapData.value = mapRes.data;
      if (mapRes.config) {
        frontendConfig.value = mapRes.config;
      }
      const regionMap = new Map();
      mapRes.regions.forEach(r => regionMap.set(r.id, r));
      regions.value = regionMap;
      isLoaded.value = true;
      console.log('[MapStore] Map preloaded');
    } catch (e) {
      console.warn('[MapStore] Failed to preload map', e);
      throw e;
    }
  }

  function reset() {
    mapData.value = [];
    regions.value = new Map();
    frontendConfig.value = {};
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
