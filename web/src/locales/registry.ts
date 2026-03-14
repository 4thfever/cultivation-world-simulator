// Keep this file aligned with tools/i18n/locales.json until we add codegen.
export const defaultLocale = 'zh-CN' as const
export const fallbackLocale = 'en-US' as const
export const schemaLocale = 'en-US' as const

export const localeRegistry = [
  {
    code: 'zh-CN',
    label: '简体中文',
    htmlLang: 'zh-CN',
    enabled: true,
  },
  {
    code: 'zh-TW',
    label: '繁體中文',
    htmlLang: 'zh-TW',
    enabled: true,
  },
  {
    code: 'en-US',
    label: 'English',
    htmlLang: 'en',
    enabled: true,
  },
] as const

export type AppLocale = (typeof localeRegistry)[number]['code']

export const enabledLocales = localeRegistry
  .filter((locale) => locale.enabled)
  .map((locale) => locale.code) as AppLocale[]

export function getHtmlLang(locale: string): string {
  return localeRegistry.find((item) => item.code === locale)?.htmlLang || 'en'
}
