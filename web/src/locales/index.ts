import { createI18n } from 'vue-i18n';
import {
  defaultLocale,
  enabledLocales,
  fallbackLocale,
  schemaLocale,
  type AppLocale,
} from './registry';

/**
 * 自动加载指定语言目录下的所有 JSON 模块
 * @param lang 语言标识符 (如 'zh-CN')
 */
const localeModuleLoaders: Record<AppLocale, Record<string, any>> = {
  'zh-CN': import.meta.glob('./zh-CN/*.json', { eager: true }),
  'zh-TW': import.meta.glob('./zh-TW/*.json', { eager: true }),
  'en-US': import.meta.glob('./en-US/*.json', { eager: true }),
};

const loadLocaleMessages = (lang: AppLocale) => {
  const messages: Record<string, any> = {};
  const modules = localeModuleLoaders[lang];

  for (const path in modules) {
    // 提取文件名作为 key，例如 ./zh-CN/ui.json -> ui
    const matched = path.match(/\/([^/]+)\.json$/);
    if (matched && matched[1]) {
      const key = matched[1];
      messages[key] = (modules[path] as any).default;
    }
  }
  return messages;
};

const messages = Object.fromEntries(
  enabledLocales.map((locale) => [locale, loadLocaleMessages(locale)])
) as Record<AppLocale, Record<string, any>>;

// 使用 schemaLocale 作为主架构进行类型推导
type MessageSchema = typeof messages[typeof schemaLocale];

const i18n = createI18n<[MessageSchema], AppLocale>({
  legacy: false, // 使用 Composition API 模式
  locale: defaultLocale, // 启动后由 settings store 统一 hydrate
  fallbackLocale, // 回退语言
  messages: messages as any
});

export default i18n;
