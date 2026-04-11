import { defineStore } from 'pinia';
import { ref, shallowRef, computed } from 'vue';
import type { CelestialPhenomenon, HiddenDomainInfo } from '../types/core';
import type { TickPayloadDTO } from '../types/api';
import { worldApi } from '../api';
import type { WorldStateSnapshot } from '../api/mappers/world';
import { logError, logWarn } from '../utils/appError';
import { useMapStore } from './map';
import { useAvatarStore } from './avatar';
import { useEventStore } from './event';
import { useSectStore } from './sect';
import { useMortalStore } from './mortal';
import { useDynastyStore } from './dynasty';
import { useAvatarOverviewStore } from './avatarOverview';

const PHENOMENON_RARITY_ORDER: Record<string, number> = {
  N: 0,
  R: 1,
  SR: 2,
  SSR: 3,
};

function sortPhenomenaByRarity(phenomena: CelestialPhenomenon[]): CelestialPhenomenon[] {
  return [...phenomena].sort((left, right) => {
    const rarityDiff =
      (PHENOMENON_RARITY_ORDER[left.rarity] ?? Number.MAX_SAFE_INTEGER) -
      (PHENOMENON_RARITY_ORDER[right.rarity] ?? Number.MAX_SAFE_INTEGER);

    if (rarityDiff !== 0) {
      return rarityDiff;
    }

    return left.id - right.id;
  });
}

export const useWorldStore = defineStore('world', () => {
  const mapStore = useMapStore();
  const avatarStore = useAvatarStore();
  const eventStore = useEventStore();
  const sectStore = useSectStore();
  const mortalStore = useMortalStore();
  const dynastyStore = useDynastyStore();
  const avatarOverviewStore = useAvatarOverviewStore();

  const year = ref(0);
  const month = ref(0);
  const startYear = ref(0);
  const startMonth = ref(0);
  const currentPhenomenon = ref<CelestialPhenomenon | null>(null);
  const phenomenaList = shallowRef<CelestialPhenomenon[]>([]);
  const activeDomains = shallowRef<HiddenDomainInfo[]>([]);
  
  // Is world loaded (map + initial state)
  const isLoaded = ref(false);

  // Request counter for fetchState
  let fetchStateRequestId = 0;

  // --- Actions ---

  function setTime(y: number, m: number) {
    year.value = y;
    month.value = m;
  }

  function handleTick(payload: TickPayloadDTO) {
    if (!isLoaded.value) return;
    
    setTime(payload.year, payload.month);

    if (payload.avatars) avatarStore.updateAvatars(payload.avatars);
    if (payload.events) eventStore.addEvents(payload.events, year.value, month.value);
    
    if (payload.phenomenon !== undefined) {
        currentPhenomenon.value = payload.phenomenon;
    }
    
    if (payload.active_domains !== undefined) {
        activeDomains.value = payload.active_domains;
    } else {
        activeDomains.value = [];
    }

    void sectStore.refreshTerritories();
  }

  function applyStateSnapshot(stateRes: WorldStateSnapshot) {
    setTime(stateRes.year, stateRes.month);
    startYear.value = stateRes.year;
    startMonth.value = stateRes.month;
    avatarStore.setAvatarsFromState(stateRes);
    
    // Reset events via store
    eventStore.reset();

    currentPhenomenon.value = stateRes.phenomenon;
    activeDomains.value = stateRes.activeDomains;
    isLoaded.value = true;
  }

  async function preloadMap() {
    await mapStore.preloadMap();
  }

  async function preloadAvatars() {
    try {
      const timeInfo = await avatarStore.preloadAvatars();
      if (timeInfo) {
        setTime(timeInfo.year, timeInfo.month);
      }
    } catch (e) {
      logWarn('WorldStore preload avatars', e);
    }
  }

  async function initialize() {
    try {
      const needMapLoad = mapStore.mapData.length === 0;
      
      if (needMapLoad) {
        // Load map and state in parallel
        const [stateRes] = await Promise.all([
          worldApi.fetchInitialState(),
          mapStore.preloadMap() // This handles mapRes internally
        ]);
        applyStateSnapshot(stateRes);
      } else {
        // Map already loaded
        const stateRes = await worldApi.fetchInitialState();
        applyStateSnapshot(stateRes);
      }

      // Load initial events
      await eventStore.resetEvents({});
      await sectStore.refreshTerritories();

    } catch (e) {
      logError('WorldStore initialize', e);
    }
  }

  async function fetchState() {
    const currentRequestId = ++fetchStateRequestId;
    try {
      const stateRes = await worldApi.fetchInitialState();
      if (currentRequestId !== fetchStateRequestId) return;
      applyStateSnapshot(stateRes);
      await sectStore.refreshTerritories();
    } catch (e) {
      if (currentRequestId !== fetchStateRequestId) return;
      logError('WorldStore fetch state', e);
    }
  }

  function reset() {
    year.value = 0;
    month.value = 0;
    startYear.value = 0;
    startMonth.value = 0;
    currentPhenomenon.value = null;
    activeDomains.value = [];
    isLoaded.value = false;
    
    avatarStore.reset();
    eventStore.reset();
    sectStore.reset();
    mortalStore.reset();
    dynastyStore.reset();
    avatarOverviewStore.reset();
    mapStore.reset();
  }

  async function getPhenomenaList() {
    if (phenomenaList.value.length > 0) return phenomenaList.value;
    try {
      const res = await worldApi.fetchPhenomenaList();
      phenomenaList.value = sortPhenomenaByRarity(res);
      return phenomenaList.value;
    } catch (e) {
      logError('WorldStore fetch phenomena list', e);
      return [];
    }
  }

  async function changePhenomenon(id: number) {
    await worldApi.setPhenomenon(id);
    const p = phenomenaList.value.find(item => item.id === id);
    if (p) {
      currentPhenomenon.value = p;
    }
  }

  // Backward-compatible proxies (gradually migrated by components/tests).
  const avatars = computed(() => avatarStore.avatars);
  const avatarList = computed(() => avatarStore.avatarList);
  const elapsedMonths = computed(() => {
    if (startYear.value <= 0 || startMonth.value <= 0 || year.value <= 0 || month.value <= 0) {
      return 0;
    }
    return Math.max(0, (year.value - startYear.value) * 12 + (month.value - startMonth.value));
  });
  const mapData = computed(() => mapStore.mapData);
  const regions = computed(() => mapStore.regions);
  const renderConfig = computed(() => mapStore.renderConfig);
  const events = computed(() => eventStore.events);
  const eventsCursor = computed(() => eventStore.eventsCursor);
  const eventsHasMore = computed(() => eventStore.eventsHasMore);
  const eventsLoading = computed(() => eventStore.eventsLoading);
  const eventsFilter = computed(() => eventStore.eventsFilter);

  return {
    // State
    year,
    month,
    startYear,
    startMonth,
    elapsedMonths,
    currentPhenomenon,
    phenomenaList,
    activeDomains,
    isLoaded,

    // Deprecated proxies.
    avatars,
    avatarList,
    mapData,
    regions,
    renderConfig,
    events,
    eventsCursor,
    eventsHasMore,
    eventsLoading,
    eventsFilter,
    
    // Actions
    preloadMap,
    preloadAvatars,
    initialize,
    fetchState,
    handleTick,
    reset,
    getPhenomenaList,
    changePhenomenon,

    // Deprecated event proxies.
    loadEvents: eventStore.loadEvents,
    loadMoreEvents: eventStore.loadMoreEvents,
    resetEvents: eventStore.resetEvents
  };
});
