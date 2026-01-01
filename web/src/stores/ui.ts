import { defineStore } from 'pinia';
import { ref } from 'vue';
import { gameApi } from '../api/game';
import type { AvatarDetail, RegionDetail, SectDetail, HoverLine } from '../types/core';

export type SelectionType = 'avatar' | 'region' | 'sect';

export interface Selection {
  type: SelectionType;
  id: string;
}

export const useUiStore = defineStore('ui', () => {
  // --- Selection & Panels ---
  
  const selectedTarget = ref<Selection | null>(null);
  
  // 详情数据 (可能为空，或正在加载)
  const detailData = ref<AvatarDetail | RegionDetail | SectDetail | null>(null);
  const isLoadingDetail = ref(false);
  const detailError = ref<string | null>(null);

  // --- Hover ---
  
  const hoveringTarget = ref<Selection | null>(null);
  const hoverInfo = ref<HoverLine[]>([]);
  
  // --- Actions ---

  async function select(type: SelectionType, id: string) {
    if (selectedTarget.value?.type === type && selectedTarget.value?.id === id) {
      return; // Already selected
    }
    
    selectedTarget.value = { type, id };
    detailData.value = null; // Reset current data
    
    await refreshDetail();
  }

  function clearSelection() {
    selectedTarget.value = null;
    detailData.value = null;
    detailError.value = null;
  }

  async function refreshDetail() {
    if (!selectedTarget.value) return;

    const target = { ...selectedTarget.value };
    isLoadingDetail.value = true;
    detailError.value = null;

    try {
      const data = await gameApi.fetchDetailInfo(target);
      
      // Race condition check: user might have changed selection
      if (
        selectedTarget.value?.type === target.type && 
        selectedTarget.value?.id === target.id
      ) {
        detailData.value = data as any; // Cast DTO to Domain Model (assuming compatibility for now)
      }
    } catch (e) {
      if (
        selectedTarget.value?.type === target.type && 
        selectedTarget.value?.id === target.id
      ) {
        detailError.value = e instanceof Error ? e.message : 'Failed to load detail';
      }
    } finally {
      if (
        selectedTarget.value?.type === target.type && 
        selectedTarget.value?.id === target.id
      ) {
        isLoadingDetail.value = false;
      }
    }
  }

  // --- Hover Actions ---

  // Simple cache for hover
  const hoverCache = new Map<string, HoverLine[]>();

  async function setHover(type: SelectionType | null, id?: string) {
    if (!type || !id) {
      hoveringTarget.value = null;
      return;
    }

    const key = `${type}:${id}`;
    hoveringTarget.value = { type, id };
    
    // Check cache
    if (hoverCache.has(key)) {
      hoverInfo.value = hoverCache.get(key)!;
      return;
    }

    try {
      const res = await gameApi.fetchHoverInfo({ type, id });
      // Normalize lines... (Assuming backend returns lines compatible with HoverLine)
      const lines = res.lines as HoverLine[]; 
      hoverCache.set(key, lines);
      
      if (hoveringTarget.value?.type === type && hoveringTarget.value?.id === id) {
        hoverInfo.value = lines;
      }
    } catch (e) {
      console.warn('Hover fetch failed', e);
    }
  }

  function clearHoverCache() {
    hoverCache.clear();
  }

  return {
    selectedTarget,
    detailData,
    isLoadingDetail,
    detailError,
    
    hoveringTarget,
    hoverInfo,
    
    select,
    clearSelection,
    refreshDetail,
    setHover,
    clearHoverCache
  };
});

