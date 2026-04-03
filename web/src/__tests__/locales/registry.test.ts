import { describe, expect, it } from 'vitest'

import { defaultLocale, getHtmlLang } from '@/locales/registry'

describe('locale registry', () => {
  it('falls back to the default locale html lang for unknown locales', () => {
    expect(getHtmlLang('unknown-locale')).toBe(getHtmlLang(defaultLocale))
  })
})
