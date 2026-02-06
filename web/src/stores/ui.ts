import { defineStore } from 'pinia';
import { ref, shallowRef } from 'vue';
import { avatarApi } from '../api';
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
  // 使用 shallowRef 避免深层响应式转换带来的性能开销 (对于大型嵌套对象，如 AvatarDetail)
  const detailData = shallowRef<AvatarDetail | RegionDetail | SectDetail | null>(null);
  const isLoadingDetail = ref(false);
  const detailError = ref<string | null>(null);

  // 请求计数器，用于处理竞态条件。
  let detailRequestId = 0;

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

    // 每次请求增加计数器，只接受最新请求的响应。
    const currentRequestId = ++detailRequestId;
    const target = { ...selectedTarget.value };
    isLoadingDetail.value = true;
    detailError.value = null;

    // 检查是否应该接受响应：requestId 匹配且 target 未变化。
    const shouldAcceptResponse = () =>
      currentRequestId === detailRequestId &&
      selectedTarget.value?.type === target.type &&
      selectedTarget.value?.id === target.id;

    try {
      const data = await avatarApi.fetchDetailInfo(target);
      
      if (shouldAcceptResponse()) {
        detailData.value = data as any;
      }
    } catch (e) {
      if (shouldAcceptResponse()) {
        detailError.value = e instanceof Error ? e.message : 'Failed to load detail';
      }
    } finally {
      if (shouldAcceptResponse()) {
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

