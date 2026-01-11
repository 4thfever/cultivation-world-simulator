import { defineStore } from 'pinia';
import { ref, shallowRef, computed } from 'vue';
import type { AvatarSummary, GameEvent, MapMatrix, RegionSummary, CelestialPhenomenon } from '../types/core';
import type { TickPayloadDTO, InitialStateDTO } from '../types/api';
import type { FetchEventsParams } from '../types/api';
import { worldApi, eventApi } from '../api';
import { processNewEvents, mergeAndSortEvents } from '../utils/eventHelper';

export const useWorldStore = defineStore('world', () => {
  // --- State ---
  
  const year = ref(0);
  const month = ref(0);
  
  // 使用 shallowRef 存储大量数据以优化性能
  // Key: Avatar ID
  const avatars = shallowRef<Map<string, AvatarSummary>>(new Map());
  
  const events = shallowRef<GameEvent[]>([]);

  // 分页状态
  const eventsCursor = ref<string | null>(null);
  const eventsHasMore = ref(false);
  const eventsLoading = ref(false);
  const eventsFilter = ref<FetchEventsParams>({});

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

    let newEvents = processNewEvents(rawEvents, year.value, month.value);

    // 根据当前筛选条件过滤（数据在 SQLite 中不会丢失）
    const filter = eventsFilter.value;
    if (filter.avatar_id) {
      newEvents = newEvents.filter(e =>
        e.relatedAvatarIds?.includes(filter.avatar_id!)
      );
    } else if (filter.avatar_id_1 && filter.avatar_id_2) {
      newEvents = newEvents.filter(e =>
        e.relatedAvatarIds?.includes(filter.avatar_id_1!) &&
        e.relatedAvatarIds?.includes(filter.avatar_id_2!)
      );
    }

    if (newEvents.length === 0) return;

    // 使用通用合并排序函数，确保顺序正确（基于 createdAt 或时间戳）
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
    // 事件通过 resetEvents() 从分页 API 加载，这里只重置状态。
    events.value = [];
    eventsCursor.value = null;
    eventsHasMore.value = false;
    eventsFilter.value = {};
    currentPhenomenon.value = stateRes.phenomenon || null;
    isLoaded.value = true;
  }

  // 提前加载地图数据（在 LLM 初始化期间可用）。
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
      // 标记地图已加载，让 MapLayer 可以渲染。
      isLoaded.value = true;
      console.log('[WorldStore] Map preloaded');
    } catch (e) {
      console.warn('[WorldStore] Failed to preload map, will retry on initialize', e);
    }
  }

  // 提前加载角色数据（在 checking_llm 阶段 world 已创建）。
  async function preloadAvatars() {
    try {
      const stateRes = await worldApi.fetchInitialState();
      // 只更新角色，不标记完全初始化。
      const avatarMap = new Map();
      if (stateRes.avatars) {
        stateRes.avatars.forEach(av => avatarMap.set(av.id, av));
      }
      avatars.value = avatarMap;
      setTime(stateRes.year, stateRes.month);
      console.log('[WorldStore] Avatars preloaded:', avatarMap.size);
    } catch (e) {
      console.warn('[WorldStore] Failed to preload avatars, will retry on initialize', e);
    }
  }

  async function initialize() {
    try {
      // 如果地图还没加载，一起加载。
      const needMapLoad = mapData.value.length === 0;
      
      if (needMapLoad) {
        const [stateRes, mapRes] = await Promise.all([
          worldApi.fetchInitialState(),
          worldApi.fetchMap()
        ]);

        mapData.value = mapRes.data;
        if (mapRes.config) {
          frontendConfig.value = mapRes.config;
        }
        const regionMap = new Map();
        mapRes.regions.forEach(r => regionMap.set(r.id, r));
        regions.value = regionMap;

        applyStateSnapshot(stateRes);
      } else {
        // 地图已预加载，只需获取状态。
        const stateRes = await worldApi.fetchInitialState();
        applyStateSnapshot(stateRes);
      }

      // 从分页 API 加载事件。
      await resetEvents({});

    } catch (e) {
      console.error('Failed to initialize world', e);
    }
  }

  async function fetchState() {
    try {
      const stateRes = await worldApi.fetchInitialState();
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
    eventsCursor.value = null;
    eventsHasMore.value = false;
    eventsFilter.value = {};
    isLoaded.value = false;
    currentPhenomenon.value = null;
  }

  // --- 事件分页 ---

  async function loadEvents(filter: FetchEventsParams = {}, append = false) {
    if (eventsLoading.value) return;
    eventsLoading.value = true;

    try {
      const params: FetchEventsParams = { ...filter, limit: 100 };
      if (append && eventsCursor.value) {
        params.cursor = eventsCursor.value;
      }

      const res = await eventApi.fetchEvents(params);

      // 转换为 GameEvent 格式
      const newEvents: GameEvent[] = res.events.map(e => ({
        id: e.id,
        text: e.text,
        content: e.content,
        year: e.year,
        month: e.month,
        timestamp: e.month_stamp,
        monthStamp: e.month_stamp,
        relatedAvatarIds: e.related_avatar_ids,
        isMajor: e.is_major,
        isStory: e.is_story,
        createdAt: e.created_at,
      }));

      // API 返回倒序（最新在前），反转成时间正序（最旧在前，最新在后）
      const sortedNewEvents = newEvents.reverse();

      if (append) {
        // 加载更旧的事件，添加到顶部。
        events.value = [...sortedNewEvents, ...events.value];
      } else {
        // 切换筛选条件：直接用 API 数据替换，不做 merge。
        // TODO: API 请求期间 WebSocket 推送的事件可能丢失，用户可手动刷新。
        events.value = sortedNewEvents;
        eventsFilter.value = filter;
      }

      eventsCursor.value = res.next_cursor;
      eventsHasMore.value = res.has_more;
    } catch (e) {
      console.error('Failed to load events', e);
    } finally {
      eventsLoading.value = false;
    }
  }

  async function loadMoreEvents() {
    if (!eventsHasMore.value || eventsLoading.value) return;
    await loadEvents(eventsFilter.value, true);
  }

  async function resetEvents(filter: FetchEventsParams = {}) {
    eventsLoading.value = false;  // 强制允许新请求，避免被旧请求阻塞。
    eventsCursor.value = null;
    eventsHasMore.value = false;
    events.value = [];  // 清空旧数据，避免筛选切换时显示残留。
    eventsFilter.value = filter;  // 立即更新筛选条件，让 addEvents 也能正确过滤。
    await loadEvents(filter, false);
  }

  async function getPhenomenaList() {
    if (phenomenaList.value.length > 0) return phenomenaList.value;
    try {
      const res = await worldApi.fetchPhenomenaList();
      // The API returns DTOs which match CelestialPhenomenon structure enough for frontend display
      phenomenaList.value = res.phenomena as CelestialPhenomenon[];
      return phenomenaList.value;
    } catch (e) {
      console.error(e);
      return [];
    }
  }

  async function changePhenomenon(id: number) {
    await worldApi.setPhenomenon(id);
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
    eventsCursor,
    eventsHasMore,
    eventsLoading,
    eventsFilter,
    mapData,
    regions,
    isLoaded,
    frontendConfig,
    currentPhenomenon,
    phenomenaList,
    
    preloadMap,
    preloadAvatars,
    initialize,
    fetchState,
    handleTick,
    reset,
    loadEvents,
    loadMoreEvents,
    resetEvents,
    getPhenomenaList,
    changePhenomenon
  };
});
