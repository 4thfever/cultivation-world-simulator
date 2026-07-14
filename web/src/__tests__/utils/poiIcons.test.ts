import { describe, expect, it } from 'vitest'
import { POI_ICON_URLS, resolvePoiIcon } from '@/utils/poiIcons'

describe('poiIcons', () => {
  const graveIconKeys = [
    'grave_01',
    'grave_02',
    'grave_03',
    'grave_04',
    'grave_05',
    'grave_06',
    'grave_07',
    'grave_08',
    'grave_09',
  ]

  it('registers all Phase 1 grave icon assets and fallback', () => {
    for (const key of graveIconKeys) {
      expect(POI_ICON_URLS[key]).toContain(`${key}.png`)
    }
    expect(POI_ICON_URLS.fallback_poi).toContain('fallback_poi.png')
  })

  it('resolves known POI icons and falls back for missing keys', () => {
    expect(resolvePoiIcon('grave_03')).toBe(POI_ICON_URLS.grave_03)
    expect(resolvePoiIcon('unknown_grave')).toBe(POI_ICON_URLS.fallback_poi)
    expect(resolvePoiIcon()).toBe(POI_ICON_URLS.fallback_poi)
  })
})
