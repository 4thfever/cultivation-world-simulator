import { defineStore } from 'pinia';
import { ref, shallowRef, computed } from 'vue';
import type { AvatarSummary, GameEvent, MapMatrix, RegionSummary, CelestialPhenomenon } from '../types/core';
import type { TickPayloadDTO, InitialStateDTO } from '../types/api';
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
    
    // 转换 DTO -> Domain
    // 增加临时索引 _seq 记录原始逻辑顺序，用于同时间戳事件的排序
    const newEvents: GameEvent[] = rawEvents.map((e, index) => ({
      id: e.id,
      text: e.text,
      content: e.content,
      year: e.year ?? year.value,
      month: e.month ?? month.value,
      timestamp: (e.year ?? year.value) * 12 + (e.month ?? month.value),
      relatedAvatarIds: e.related_avatar_ids || [],
      isMajor: e.is_major,
      isStory: e.is_story,
      _seq: index 
    } as GameEvent & { _seq: number }));

    // 排序并保留最新的 N 条
    const MAX_EVENTS = 300;
    const combined = [...newEvents, ...events.value];
    
    combined.sort((a, b) => {
      // 1. 先按时间戳升序（最旧的月在上面）
      const ta = a.timestamp;
      const tb = b.timestamp;
      if (tb !== ta) {
        return ta - tb;
      }
      
      // 2. 时间相同时，按原始逻辑顺序升序（先发生的在上面）
      // 旧事件通常没有 _seq (undefined)，视为最旧 (-1)
      const seqA = (a as any)._seq ?? -1;
      const seqB = (b as any)._seq ?? -1;
      
      // 如果都是旧事件，保持相对顺序 (Stable)
      if (seqA === -1 && seqB === -1) return 0;
      
      return seqA - seqB;
    });
    
    // 保留最新的 N 条 (因为是升序，最新的在最后，所以取最后 N 条)
    if (combined.length > MAX_EVENTS) {
      events.value = combined.slice(-MAX_EVENTS);
    } else {
      events.value = combined;
    }
  }

  function handleTick(payload: TickPayloadDTO) {
    if (!isLoaded.value) return;
    
    setTime(payload.year, payload.month);

    // 检查并处理死亡事件，移除已死亡的角色
    if (payload.events && Array.isArray(payload.events)) {
      const deathEvents = (payload.events as any[]).filter((e: any) => {
        const c = e.content || '';
        return c.includes('身亡') || c.includes('老死');
      });

      if (deathEvents.length > 0) {
        const next = new Map(avatars.value);
        let changed = false;

        for (const de of deathEvents) {
          if (de.related_avatar_ids && Array.isArray(de.related_avatar_ids)) {
            for (const id of de.related_avatar_ids) {
              if (next.has(id)) {
                next.delete(id);
                changed = true;
              }
            }
          }
        }

        if (changed) {
          avatars.value = next;
        }
      }
    }

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
