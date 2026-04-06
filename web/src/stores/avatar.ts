import { defineStore } from 'pinia';
import { shallowRef, computed } from 'vue';
import type { AvatarSummary } from '../types/core';
import type { WorldStateSnapshot } from '../api/mappers/world';
import { worldApi } from '../api';
import { logWarn } from '../utils/appError';

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

  function updateAvatarSummary(id: string, patch: Partial<AvatarSummary>) {
    const existing = avatars.value.get(id);
    if (!existing) return;
    avatars.value = new Map(avatars.value).set(id, {
      ...existing,
      ...patch,
      id: existing.id,
    });
  }

  async function preloadAvatars() {
    try {
      const stateRes = await worldApi.fetchInitialState();
      const avatarMap = new Map<string, AvatarSummary>();
      stateRes.avatars.forEach(av => avatarMap.set(av.id, av));
      avatars.value = avatarMap;
      // Return state info that might be useful for world store (e.g. time)
      return { year: stateRes.year, month: stateRes.month };
    } catch (e) {
      logWarn('AvatarStore preload avatars', e);
      throw e;
    }
  }

  function setAvatarsFromState(stateRes: WorldStateSnapshot) {
    const avatarMap = new Map<string, AvatarSummary>();
    stateRes.avatars.forEach(av => avatarMap.set(av.id, av));
    avatars.value = avatarMap;
  }

  function reset() {
    avatars.value = new Map();
  }

  return {
    avatars,
    avatarList,
    updateAvatars,
    updateAvatarSummary,
    preloadAvatars,
    setAvatarsFromState,
    reset
  };
});
