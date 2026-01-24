import { defineStore } from 'pinia';
import { ref } from 'vue';
import { gameSocket } from '../api/socket';
import { useWorldStore } from './world';
import { useUiStore } from './ui';
import type { TickPayloadDTO } from '../types/api';
import { message } from '../utils/discreteApi';
import i18n from '../locales';

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
        
        // Refresh Detail if open (Silent update)
        if (uiStore.selectedTarget) {
          uiStore.refreshDetail(); 
        }
      }
      // ===== 处理 Toast 消息 (含语言切换) =====
      else if (data.type === 'toast') {
        const { level, message: msg, language } = data;
        
        // 显示 Toast
        if (level === 'error') message.error(msg);
        else if (level === 'warning') message.warning(msg);
        else if (level === 'success') message.success(msg);
        else message.info(msg);

        // 如果包含语言字段，则切换前端语言
        if (language) {
          try {
            const currentLang = i18n.mode === 'legacy' 
                ? (i18n.global.locale as any) 
                : (i18n.global.locale as any).value;
            
            if (currentLang !== language) {
               if (i18n.mode === 'legacy') {
                   (i18n.global.locale as any) = language;
               } else {
                   (i18n.global.locale as any).value = language;
               }
               localStorage.setItem('app_locale', language);
               
               // 更新 HTML lang 属性
               document.documentElement.lang = language === 'zh-CN' ? 'zh-CN' : 'en';
               
               console.log(`[Socket] Frontend language switched to ${language}`);
            }
          } catch (e) {
            console.error('[Socket] Failed to switch language:', e);
          }
        }
      }
      // ===== 处理 LLM 配置要求消息 =====
      else if (data.type === 'llm_config_required') {
        console.warn('LLM 配置要求:', data.error);
        
        // 显示错误提示
        const message = data.error || 'LLM 连接失败，请配置';
        
        // 通过全局方法打开 LLM 配置界面
        if ((window as any).__openLLMConfig) {
          (window as any).__openLLMConfig();
        }
        
        // 可以选择在这里显示一个提示消息
        // 需要引入 message API 或者通过其他方式
        setTimeout(() => {
          alert(`${message}\n\n请在打开的配置界面中完成 LLM 设置。`);
        }, 500);
      }
      // ===== 处理游戏重新初始化消息 =====
      else if (data.type === 'game_reinitialized') {
        console.log('游戏重新初始化:', data.message);
        
        // 刷新世界状态
        worldStore.initialize().catch(console.error);
        
        // 显示成功提示
        setTimeout(() => {
          alert(data.message || 'LLM 配置成功，游戏已重新初始化');
        }, 300);
      }
      // ===== LLM 消息处理结束 =====
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

