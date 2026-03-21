import { defineStore } from 'pinia';
import { ref, shallowRef, computed } from 'vue';
import type { CelestialPhenomenon, HiddenDomainInfo } from '../types/core';
import type { TickPayloadDTO, InitialStateDTO } from '../types/api';
import { worldApi } from '../api';
import { logError, logWarn } from '../utils/appError';
import { useMapStore } from './map';
import { useAvatarStore } from './avatar';
import { useEventStore } from './event';
import { useSectStore } from './sect';
import { useMortalStore } from './mortal';
import { useDynastyStore } from './dynasty';

export const useWorldStore = defineStore('world', () => {
  const mapStore = useMapStore();
  const avatarStore = useAvatarStore();
  const eventStore = useEventStore();
  const sectStore = useSectStore();
  const mortalStore = useMortalStore();
  const dynastyStore = useDynastyStore();

  const year = ref(0);
  const month = ref(0);
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

  function applyStateSnapshot(stateRes: InitialStateDTO) {
    setTime(stateRes.year, stateRes.month);
    avatarStore.setAvatarsFromState(stateRes);
    
    // Reset events via store
    eventStore.reset();

    currentPhenomenon.value = stateRes.phenomenon || null;
    isLoaded.value = true;
    activeDomains.value = [];
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
    currentPhenomenon.value = null;
    activeDomains.value = [];
    isLoaded.value = false;
    
    avatarStore.reset();
    eventStore.reset();
    sectStore.reset();
    mortalStore.reset();
    dynastyStore.reset();
    mapStore.reset();
  }

  async function getPhenomenaList() {
    if (phenomenaList.value.length > 0) return phenomenaList.value;
    try {
      const res = await worldApi.fetchPhenomenaList();
      phenomenaList.value = res.phenomena as CelestialPhenomenon[];
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
  const mapData = computed(() => mapStore.mapData);
  const regions = computed(() => mapStore.regions);
  const frontendConfig = computed(() => mapStore.frontendConfig);
  const events = computed(() => eventStore.events);
  const eventsCursor = computed(() => eventStore.eventsCursor);
  const eventsHasMore = computed(() => eventStore.eventsHasMore);
  const eventsLoading = computed(() => eventStore.eventsLoading);
  const eventsFilter = computed(() => eventStore.eventsFilter);

  return {
    // State
    year,
    month,
    currentPhenomenon,
    phenomenaList,
    activeDomains,
    isLoaded,

    // Deprecated proxies.
    avatars,
    avatarList,
    mapData,
    regions,
    frontendConfig,
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
