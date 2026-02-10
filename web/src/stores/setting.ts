import { defineStore } from 'pinia';
import { ref } from 'vue';
import i18n from '../locales';
import { systemApi } from '../api/modules/system';

export const useSettingStore = defineStore('setting', () => {
  const locale = ref(localStorage.getItem('app_locale') || 'zh-CN');
  
  // Sound settings
  const sfxVolume = ref(parseFloat(localStorage.getItem('app_sfx_volume') || '0.5'));
  const bgmVolume = ref(parseFloat(localStorage.getItem('app_bgm_volume') || '0.5'));

  function setSfxVolume(volume: number) {
    sfxVolume.value = volume;
    localStorage.setItem('app_sfx_volume', String(volume));
  }

  function setBgmVolume(volume: number) {
    bgmVolume.value = volume;
    localStorage.setItem('app_bgm_volume', String(volume));
  }

  async function setLocale(lang: 'zh-CN' | 'zh-TW' | 'en-US') {
    // 1. Optimistic UI update
    locale.value = lang;
    localStorage.setItem('app_locale', lang);
    if (i18n.mode === 'legacy') {
        (i18n.global.locale as any) = lang;
    } else {
        (i18n.global.locale as any).value = lang;
    }
    // Update HTML lang attribute for accessibility
    const langMap: Record<string, string> = {
      'zh-CN': 'zh-CN',
      'zh-TW': 'zh-TW',
      'en-US': 'en'
    };
    document.documentElement.lang = langMap[lang] || 'en';

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
    syncBackend,
    sfxVolume,
    bgmVolume,
    setSfxVolume,
    setBgmVolume
  };
});
