import { defineStore } from 'pinia';
import { ref } from 'vue';
import { gameApi } from '../api/game';
import type { AvatarDetail, RegionDetail, SectDetail } from '../types/core';

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

  function clearHoverCache() {
    // 清除详情缓存，强制下次选择时重新加载。
    detailData.value = null;
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

  return {
    selectedTarget,
    detailData,
    isLoadingDetail,
    detailError,

    select,
    clearSelection,
    clearHoverCache,
    refreshDetail
  };
});

