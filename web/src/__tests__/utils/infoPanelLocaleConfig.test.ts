import { describe, expect, it } from 'vitest'
import { getEntityRowDetailLayout } from '@/utils/infoPanelLocaleConfig'

describe('infoPanelLocaleConfig', () => {
  it('uses explicit entity row layout config for supported locales', () => {
    expect(getEntityRowDetailLayout('zh-CN')).toBe('inline-preferred')
    expect(getEntityRowDetailLayout('zh-TW')).toBe('inline-preferred')
    expect(getEntityRowDetailLayout('ja-JP')).toBe('inline-preferred')
    expect(getEntityRowDetailLayout('en-US')).toBe('stacked')
    expect(getEntityRowDetailLayout('vi-VN')).toBe('stacked')
  })

  it('falls back by locale prefix and defaults to stacked', () => {
    expect(getEntityRowDetailLayout('zh-SG')).toBe('inline-preferred')
    expect(getEntityRowDetailLayout('ja')).toBe('inline-preferred')
    expect(getEntityRowDetailLayout('en-GB')).toBe('stacked')
    expect(getEntityRowDetailLayout('fr-FR')).toBe('stacked')
    expect(getEntityRowDetailLayout('')).toBe('stacked')
  })
})
