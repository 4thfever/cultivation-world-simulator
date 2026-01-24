import { defineStore } from 'pinia';
import { ref } from 'vue';
import i18n from '../locales';
import { systemApi } from '../api/modules/system';

export const useSettingStore = defineStore('setting', () => {
  const locale = ref(localStorage.getItem('app_locale') || 'zh-CN');

  async function setLocale(lang: 'zh-CN' | 'en-US') {
    // 1. Optimistic UI update
    locale.value = lang;
    localStorage.setItem('app_locale', lang);
    if (i18n.mode === 'legacy') {
        (i18n.global.locale as any) = lang;
    } else {
        (i18n.global.locale as any).value = lang;
    }
    // Update HTML lang attribute for accessibility
    document.documentElement.lang = lang === 'zh-CN' ? 'zh-CN' : 'en';

    // 2. Sync with backend
    await syncBackend();
  }
  
  async function syncBackend() {
      try {
          await systemApi.setLanguage(locale.value);
      } catch (e) {
          console.warn('Failed to sync language with backend:', e);
      }
  }

  return {
    locale,
    setLocale,
    syncBackend
  };
});
