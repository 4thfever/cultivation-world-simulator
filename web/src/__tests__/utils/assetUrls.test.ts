import { describe, expect, it } from 'vitest'
import { getAvatarPortraitUrl, getGameAssetUrl, withBasePublicPath } from '@/utils/assetUrls'

describe('assetUrls', () => {
  it('prefixes public assets with the Vite base URL', () => {
    expect(withBasePublicPath('icons/edit.png')).toBe('/icons/edit.png')
    expect(withBasePublicPath('/sfx/click.ogg')).toBe('/sfx/click.ogg')
  })

  it('keeps game assets on the backend /assets route', () => {
    expect(getGameAssetUrl('tiles/plain.png')).toBe('/assets/tiles/plain.png')
    expect(getGameAssetUrl('/avatars/male/001/qi_refining.png')).toBe('/assets/avatars/male/001/qi_refining.png')
  })

  it('builds realm-aware avatar portrait urls from gender and pic id', () => {
    expect(getAvatarPortraitUrl('male', 3)).toBe('/assets/avatars/male/003/qi_refining.png')
    expect(getAvatarPortraitUrl('female', 8, 'FOUNDATION_ESTABLISHMENT')).toBe('/assets/avatars/female/008/foundation.png')
    expect(getAvatarPortraitUrl('女', 5, 'CORE_FORMATION')).toBe('/assets/avatars/female/005/golden_core.png')
    expect(getAvatarPortraitUrl('male', 6, 'NASCENT_SOUL')).toBe('/assets/avatars/male/006/nascent_soul.png')
    expect(getAvatarPortraitUrl('male', null)).toBe('')
  })
})
