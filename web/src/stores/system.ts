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

  // 请求计数器，用于处理竞态条件。
  let fetchStatusRequestId = 0;
  
  // --- Getters ---
  const isLoading = computed(() => {
    if (!initStatus.value) return true;
    if (initStatus.value.status === 'idle') return false;
    if (initStatus.value.status === 'ready' && isInitialized.value) return false;
    return true;
  });

  const isReady = computed(() => {
    return initStatus.value?.status === 'ready' && isInitialized.value;
  });

  // --- Actions ---
  
  async function fetchInitStatus() {
    const currentRequestId = ++fetchStatusRequestId;
    try {
      const res = await systemApi.fetchInitStatus();
      
      // 只接受最新请求的响应。
      if (currentRequestId !== fetchStatusRequestId) {
        return null;
      }
      
      initStatus.value = res;
      
      if (res.status === 'ready') {
        isGameRunning.value = true;
      } else {
        isGameRunning.value = false;
      }
      return res;
    } catch (e) {
      if (currentRequestId === fetchStatusRequestId) {
        console.error('Failed to fetch init status', e);
      }
      return null;
    }
  }

  function setInitialized(val: boolean) {
    isInitialized.value = val;
  }

  // 切换手动暂停状态（用户点击暂停按钮时调用）
  async function togglePause() {
    const newState = !isManualPaused.value;
    isManualPaused.value = newState;
    try {
      if (newState) {
        await systemApi.pauseGame();
      } else {
        await systemApi.resumeGame();
      }
    } catch (e) {
      // API 失败时回滚状态
      isManualPaused.value = !newState;
      console.error(e);
    }
  }

  // 仅调用后端 API，不修改 isManualPaused（用于菜单打开/关闭等系统行为）
  async function pause() {
    try {
      await systemApi.pauseGame();
    } catch (e) {
      console.error(e);
    }
  }

  async function resume() {
    try {
      await systemApi.resumeGame();
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
