import { defineStore } from 'pinia';
import { ref, shallowRef, computed } from 'vue';
import type { AvatarSummary, GameEvent, MapMatrix, RegionSummary } from '../types/core';
import type { TickPayloadDTO, InitialStateDTO, MapResponseDTO } from '../types/api';
import { gameApi } from '../api/game';

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
      } else {
        // Insert (ensure required fields exist if possible, otherwise cast)
        // 在 Tick 中出现的新 Avatar 可能是完整的
        next.set(av.id, av as AvatarSummary); 
      }
      changed = true;
    }

    if (changed) {
      avatars.value = next;
    }
  }

  function addEvents(rawEvents: any[]) {
    if (!rawEvents || rawEvents.length === 0) return;
    
    // 转换 DTO -> Domain
    const newEvents: GameEvent[] = rawEvents.map(e => ({
      id: e.id,
      text: e.text,
      content: e.content,
      year: e.year ?? year.value,
      month: e.month ?? month.value,
      timestamp: (e.year ?? year.value) * 12 + (e.month ?? month.value),
      relatedAvatarIds: e.relatedAvatarIds || [],
      isMajor: e.isMajor,
      isStory: e.isStory
    }));

    // 排序并保留最新的 N 条
    const MAX_EVENTS = 300;
    const combined = [...newEvents, ...events.value];
    combined.sort((a, b) => b.timestamp - a.timestamp); // 降序
    
    events.value = combined.slice(0, MAX_EVENTS);
  }

  function handleTick(payload: TickPayloadDTO) {
    setTime(payload.year, payload.month);
    if (payload.avatars) updateAvatars(payload.avatars);
    if (payload.events) addEvents(payload.events);
  }

  async function initialize() {
    try {
      const [stateRes, mapRes] = await Promise.all([
        gameApi.fetchInitialState(),
        gameApi.fetchMap()
      ]);

      // 1. Set Map
      mapData.value = mapRes.data;
      const regionMap = new Map();
      mapRes.regions.forEach(r => regionMap.set(r.id, r));
      regions.value = regionMap;

      // 2. Set State
      setTime(stateRes.year, stateRes.month);
      
      const avatarMap = new Map();
      if (stateRes.avatars) {
        stateRes.avatars.forEach(av => avatarMap.set(av.id, av));
      }
      avatars.value = avatarMap;

      // 3. Set Events (Initial state might have history?)
      events.value = [];
      if (stateRes.events) addEvents(stateRes.events);

      isLoaded.value = true;
    } catch (e) {
      console.error('Failed to initialize world', e);
    }
  }

  function reset() {
    year.value = 0;
    month.value = 0;
    avatars.value = new Map();
    events.value = [];
    isLoaded.value = false;
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
    
    initialize,
    handleTick,
    reset
  };
});

