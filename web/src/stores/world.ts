import { defineStore } from 'pinia';
import { ref, shallowRef, computed } from 'vue';
import type { AvatarSummary, GameEvent, MapMatrix, RegionSummary, CelestialPhenomenon } from '../types/core';
import type { TickPayloadDTO, InitialStateDTO } from '../types/api';
import { gameApi } from '../api/game';
import { processNewEvents, mergeAndSortEvents } from '../utils/eventHelper';

export const useWorldStore = defineStore('world', () => {
  // --- State ---
  
  const year = ref(0);
  const month = ref(0);
  
  // 使用 shallowRef 存储大量数据以优化性能
  // Key: Avatar ID
  const avatars = shallowRef<Map<string, AvatarSummary>>(new Map());
  
  const events = shallowRef<GameEvent[]>([]);
  
  const mapData = shallowRef<MapMatrix>([]);
  const regions = shallowRef<Map<string | number, RegionSummary>>(new Map());
  
  const isLoaded = ref(false);
  const frontendConfig = ref<Record<string, any>>({});
  
  const currentPhenomenon = ref<CelestialPhenomenon | null>(null);
  const phenomenaList = shallowRef<CelestialPhenomenon[]>([]);

  // --- Getters ---

  const avatarList = computed(() => Array.from(avatars.value.values()));

  // --- Actions ---

  function setTime(y: number, m: number) {
    year.value = y;
    month.value = m;
  }

  function updateAvatars(list: Partial<AvatarSummary>[]) {
    const next = new Map(avatars.value);
    let changed = false;

    for (const av of list) {
      if (!av.id) continue;
      const existing = next.get(av.id);
      if (existing) {
        // Merge
        next.set(av.id, { ...existing, ...av } as AvatarSummary);
        changed = true;
      } else {
        // New Avatar? Only insert if it has enough info (at least name)
        // This handles newly born avatars sent by backend
        if (av.name) {
           next.set(av.id, av as AvatarSummary);
           changed = true;
        }
      }
      // Else: ignore. Do NOT insert new avatars from tick updates unless they have full info.
    }

    if (changed) {
      avatars.value = next;
    }
  }

  function addEvents(rawEvents: any[]) {
    if (!rawEvents || rawEvents.length === 0) return;
    
    const newEvents = processNewEvents(rawEvents, year.value, month.value);
    events.value = mergeAndSortEvents(events.value, newEvents);
  }

  function handleTick(payload: TickPayloadDTO) {
    if (!isLoaded.value) return;
    
    setTime(payload.year, payload.month);

    if (payload.avatars) updateAvatars(payload.avatars);
    if (payload.events) addEvents(payload.events);
    if (payload.phenomenon !== undefined) {
        currentPhenomenon.value = payload.phenomenon;
    }
  }

  function applyStateSnapshot(stateRes: InitialStateDTO) {
    setTime(stateRes.year, stateRes.month);
    const avatarMap = new Map();
    if (stateRes.avatars) {
      stateRes.avatars.forEach(av => avatarMap.set(av.id, av));
    }
    avatars.value = avatarMap;
    events.value = [];
    if (stateRes.events) addEvents(stateRes.events);
    currentPhenomenon.value = stateRes.phenomenon || null;
    isLoaded.value = true;
  }

  async function initialize() {
    try {
      const [stateRes, mapRes] = await Promise.all([
        gameApi.fetchInitialState(),
        gameApi.fetchMap()
      ]);

      mapData.value = mapRes.data;
      if (mapRes.config) {
        frontendConfig.value = mapRes.config;
      }
      const regionMap = new Map();
      mapRes.regions.forEach(r => regionMap.set(r.id, r));
      regions.value = regionMap;

      applyStateSnapshot(stateRes);
    } catch (e) {
      console.error('Failed to initialize world', e);
    }
  }

  async function fetchState() {
    try {
      const stateRes = await gameApi.fetchInitialState();
      applyStateSnapshot(stateRes);
    } catch (e) {
      console.error('Failed to fetch state snapshot', e);
    }
  }

  function reset() {
    year.value = 0;
    month.value = 0;
    avatars.value = new Map();
    events.value = [];
    isLoaded.value = false;
    currentPhenomenon.value = null;
  }

  async function getPhenomenaList() {
    if (phenomenaList.value.length > 0) return phenomenaList.value;
    try {
      const res = await gameApi.fetchPhenomenaList();
      // The API returns DTOs which match CelestialPhenomenon structure enough for frontend display
      phenomenaList.value = res.phenomena as CelestialPhenomenon[];
      return phenomenaList.value;
    } catch (e) {
      console.error(e);
      return [];
    }
  }

  async function changePhenomenon(id: number) {
    await gameApi.setPhenomenon(id);
    // 乐观更新：直接从列表里找到并设置，不等下一次 tick
    const p = phenomenaList.value.find(item => item.id === id);
    if (p) {
      currentPhenomenon.value = p;
    }
  }

  return {
    year,
    month,
    avatars,
    avatarList,
    events,
    mapData,
    regions,
    isLoaded,
    frontendConfig,
    currentPhenomenon,
    phenomenaList,
    
    initialize,
    fetchState,
    handleTick,
    reset,
    getPhenomenaList,
    changePhenomenon
  };
});
