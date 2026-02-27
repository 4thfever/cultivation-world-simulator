import { createI18n } from 'vue-i18n';
import zhCN from './zh-CN.json';
import zhTW from './zh-TW.json';
import enUS from './en-US.json';
import viVN from './vi-VN.json';

// Type-define 'en-US' as the master schema for the resource
type MessageSchema = typeof enUS;

const i18n = createI18n<[MessageSchema], 'en-US' | 'zh-CN' | 'zh-TW' | 'vi-VN'>({
  legacy: false, // Use Composition API mode
  locale: localStorage.getItem('app_locale') || 'zh-CN', // Default locale
  fallbackLocale: 'en-US', // Fallback locale
  messages: {
    'zh-CN': zhCN,
    'zh-TW': zhTW,
    'en-US': enUS,
    'vi-VN': viVN
  }
});

export default i18n;

