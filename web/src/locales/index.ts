import { createI18n } from 'vue-i18n'
import {
  defaultLocale,
  enabledLocales,
  fallbackLocale,
  isEnabledLocale,
  schemaLocale,
  type AppLocale,
} from './registry'

type LocaleJsonModule = {
  default: Record<string, unknown>
}

type LocaleMessageTree = Record<string, unknown>

const localeJsonModules = import.meta.glob('./*/*.json', { eager: true }) as Record<string, LocaleJsonModule>

/**
 * 自动加载指定语言目录下的所有 JSON 模块
 * @param lang 语言标识符 (如 'zh-CN')
 */
const loadLocaleMessages = (lang: AppLocale) => {
  const messages: LocaleMessageTree = {}

  for (const [path, module] of Object.entries(localeJsonModules)) {
    const matched = path.match(/^\.\/([^/]+)\/([^/]+)\.json$/)
    if (!matched || matched[1] !== lang || !matched[2]) {
      continue
    }

    const key = matched[2]
    messages[key] = module.default
  }

  return messages
}

const messages = Object.fromEntries(
  enabledLocales.map((locale) => [locale, loadLocaleMessages(locale)])
) as Record<string, LocaleMessageTree>

const schemaMessages = isEnabledLocale(schemaLocale)
  ? loadLocaleMessages(schemaLocale)
  : {}

type MessageSchema = typeof schemaMessages
type LocaleMessages = Record<AppLocale, MessageSchema>

const i18n = createI18n<[MessageSchema], string>({
  legacy: false,
  locale: defaultLocale,
  fallbackLocale,
  messages: messages as LocaleMessages,
})

export default i18n
