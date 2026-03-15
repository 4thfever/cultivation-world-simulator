import { createI18n } from 'vue-i18n'

import {
  defaultLocale,
  fallbackLocale,
  getHtmlLang,
  type AppLocale,
} from '@/locales/registry'

export const testDefaultLocale = defaultLocale
export const testFallbackLocale = fallbackLocale

export function createTestI18n(
  messages: Record<string, unknown>,
  locale: AppLocale = testDefaultLocale,
) {
  return createI18n({
    legacy: false,
    locale,
    messages: {
      [locale]: messages,
    },
  })
}

export function createMutableLocaleState(locale: AppLocale = testDefaultLocale) {
  return { value: locale }
}

export function getExpectedHtmlLang(locale: string): string {
  return getHtmlLang(locale)
}
