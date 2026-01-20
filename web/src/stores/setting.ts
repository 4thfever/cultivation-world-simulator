import { defineStore } from 'pinia';
import { ref } from 'vue';
import i18n from '../locales';

export const useSettingStore = defineStore('setting', () => {
  const locale = ref(localStorage.getItem('app_locale') || 'zh-CN');

  function setLocale(lang: 'zh-CN' | 'en-US') {
    locale.value = lang;
    localStorage.setItem('app_locale', lang);
    if (i18n.global.mode === 'legacy') {
        (i18n.global.locale as any) = lang;
    } else {
        (i18n.global.locale as any).value = lang;
    }
    // Update HTML lang attribute for accessibility
    document.documentElement.lang = lang === 'zh-CN' ? 'zh-CN' : 'en';
  }

  return {
    locale,
    setLocale
  };
});
