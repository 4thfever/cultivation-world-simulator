import { defineStore } from 'pinia';
import { shallowRef, computed } from 'vue';
import type { AvatarSummary } from '../types/core';
import type { InitialStateDTO } from '../types/api';
import { worldApi } from '../api';

export const useAvatarStore = defineStore('avatar', () => {
  // Key: Avatar ID
  const avatars = shallowRef<Map<string, AvatarSummary>>(new Map());

  const avatarList = computed(() => Array.from(avatars.value.values()));

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
        if (av.name) {
           next.set(av.id, av as AvatarSummary);
           changed = true;
        }
      }
    }

    if (changed) {
      avatars.value = next;
    }
  }

  async function preloadAvatars() {
    try {
      const stateRes = await worldApi.fetchInitialState();
      const avatarMap = new Map();
      if (stateRes.avatars) {
        stateRes.avatars.forEach(av => avatarMap.set(av.id, av));
      }
      avatars.value = avatarMap;
      console.log('[AvatarStore] Avatars preloaded:', avatarMap.size);
      // Return state info that might be useful for world store (e.g. time)
      return { year: stateRes.year, month: stateRes.month };
    } catch (e) {
      console.warn('[AvatarStore] Failed to preload avatars', e);
      throw e;
    }
  }

  function setAvatarsFromState(stateRes: InitialStateDTO) {
    const avatarMap = new Map();
    if (stateRes.avatars) {
      stateRes.avatars.forEach(av => avatarMap.set(av.id, av));
    }
    avatars.value = avatarMap;
  }

  function reset() {
    avatars.value = new Map();
  }

  return {
    avatars,
    avatarList,
    updateAvatars,
    preloadAvatars,
    setAvatarsFromState,
    reset
  };
});
