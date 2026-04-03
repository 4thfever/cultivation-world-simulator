import localeRegistryData from '../../../static/locales/registry.json'

type LocaleRegistryFile = {
  default_locale: string
  fallback_locale: string
  schema_locale: string
  locales: Array<{
    code: string
    label: string
    html_lang: string
    enabled?: boolean
    source_of_truth?: boolean
  }>
}

type LocaleEntry = {
  code: string
  label: string
  htmlLang: string
  enabled: boolean
  sourceOfTruth: boolean
}

const registry = localeRegistryData as LocaleRegistryFile

export const defaultLocale = registry.default_locale
export const fallbackLocale = registry.fallback_locale
export const schemaLocale = registry.schema_locale

export const localeRegistry: LocaleEntry[] = registry.locales.map((locale) => ({
  code: locale.code,
  label: locale.label,
  htmlLang: locale.html_lang,
  enabled: locale.enabled !== false,
  sourceOfTruth: locale.source_of_truth === true,
}))

export type AppLocale = string

export const enabledLocales = localeRegistry
  .filter((locale) => locale.enabled)
  .map((locale) => locale.code)

const enabledLocaleSet = new Set(enabledLocales)
const defaultHtmlLang =
  localeRegistry.find((item) => item.code === defaultLocale)?.htmlLang || 'en'

export function isEnabledLocale(locale: string): boolean {
  return enabledLocaleSet.has(locale)
}

export function getHtmlLang(locale: string): string {
  return localeRegistry.find((item) => item.code === locale)?.htmlLang || defaultHtmlLang
}
