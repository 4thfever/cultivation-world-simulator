import { onMounted, onUnmounted } from 'vue';
import { gameSocket } from '../api/socket';
import { useWorldStore } from '../stores/world';
import { useUiStore } from '../stores/ui';
import type { TickPayloadDTO } from '../types/api';

export function useGameSocket() {
  const worldStore = useWorldStore();
  const uiStore = useUiStore();

  let cleanupMessage: (() => void) | undefined;
  let cleanupStatus: (() => void) | undefined;

  onMounted(() => {
    // Connect socket
    gameSocket.connect();

    // Listen for ticks
    cleanupMessage = gameSocket.on((data: any) => {
      if (data.type === 'tick') {
        const payload = data as TickPayloadDTO;
        
        // Update World
        worldStore.handleTick(payload);
        
        // UI Cache Invalidations
        uiStore.clearHoverCache();
        
        // Refresh Detail if open (Silent update)
        // 注意：这里可以选择是否每次 tick 都刷新详情，或者让用户手动刷新
        // 为了实时性，通常会尝试静默刷新
        if (uiStore.selectedTarget) {
          uiStore.refreshDetail(); 
        }
      }
    });

    // Listen for status
    cleanupStatus = gameSocket.onStatusChange((connected) => {
      console.log('Socket status:', connected ? 'Connected' : 'Disconnected');
      // Could update a connection status in a store if needed
    });
  });

  onUnmounted(() => {
    if (cleanupMessage) cleanupMessage();
    if (cleanupStatus) cleanupStatus();
    gameSocket.disconnect();
  });
}

