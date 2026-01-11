import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { systemApi } from '../api';
import type { InitStatusDTO } from '../types/api';

export const useSystemStore = defineStore('system', () => {
  // --- State ---
  const initStatus = ref<InitStatusDTO | null>(null);
  const isInitialized = ref(false); // 前端是否完成初始化 (world store loaded, socket connected)
  const isManualPaused = ref(true); // 用户手动暂停
  const isGameRunning = ref(false); // 游戏是否处于 Running 阶段 (Init Status ready)
  
  // --- Getters ---
  const isLoading = computed(() => {
    if (!initStatus.value) return true;
    if (initStatus.value.status === 'idle') return false;
    if (initStatus.value.status !== 'ready') return true;
    if (!isInitialized.value) return true;
    return false;
  });

  const isReady = computed(() => {
    return initStatus.value?.status === 'ready' && isInitialized.value;
  });

  // --- Actions ---
  
  async function fetchInitStatus() {
    try {
      const res = await systemApi.fetchInitStatus();
      initStatus.value = res;
      
      if (res.status === 'ready') {
        isGameRunning.value = true;
      } else {
        isGameRunning.value = false;
      }
      return res;
    } catch (e) {
      console.error('Failed to fetch init status', e);
      return null;
    }
  }

  function setInitialized(val: boolean) {
    isInitialized.value = val;
  }

  async function togglePause() {
    if (isManualPaused.value) {
      await resume();
    } else {
      await pause();
    }
  }

  async function pause() {
    try {
      await systemApi.pauseGame();
      isManualPaused.value = true;
    } catch (e) {
      console.error(e);
    }
  }

  async function resume() {
    try {
      await systemApi.resumeGame();
      isManualPaused.value = false;
    } catch (e) {
      console.error(e);
    }
  }

  return {
    initStatus,
    isInitialized,
    isManualPaused,
    isGameRunning,
    isLoading,
    isReady,
    
    fetchInitStatus,
    setInitialized,
    togglePause,
    pause,
    resume
  };
});
