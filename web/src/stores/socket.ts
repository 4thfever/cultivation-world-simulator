import { defineStore } from 'pinia';
import { ref } from 'vue';
import { gameSocket } from '../api/socket';
import { useWorldStore } from './world';
import { useUiStore } from './ui';
import type { TickPayloadDTO } from '../types/api';

export const useSocketStore = defineStore('socket', () => {
  const isConnected = ref(false);
  const lastError = ref<string | null>(null);
  
  let cleanupMessage: (() => void) | undefined;
  let cleanupStatus: (() => void) | undefined;

  function init() {
    if (cleanupStatus) return; // Already initialized

    const worldStore = useWorldStore();
    const uiStore = useUiStore();

    // Listen for status
    cleanupStatus = gameSocket.onStatusChange((connected) => {
      isConnected.value = connected;
      if (connected) {
        lastError.value = null;
      }
    });

    // Listen for ticks
    cleanupMessage = gameSocket.on((data: any) => {
      if (data.type === 'tick') {
        const payload = data as TickPayloadDTO;
        
        // Update World
        worldStore.handleTick(payload);
        
        // UI Cache Invalidations
        uiStore.clearHoverCache();
        
        // Refresh Detail if open (Silent update)
        if (uiStore.selectedTarget) {
          uiStore.refreshDetail(); 
        }
      }
    });

    // Connect socket
    gameSocket.connect();
  }

  function disconnect() {
    if (cleanupMessage) cleanupMessage();
    if (cleanupStatus) cleanupStatus();
    cleanupMessage = undefined;
    cleanupStatus = undefined;
    gameSocket.disconnect();
    isConnected.value = false;
  }

  return {
    isConnected,
    lastError,
    init,
    disconnect
  };
});

