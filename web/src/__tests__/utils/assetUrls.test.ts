import { describe, expect, it } from 'vitest'
import { getAvatarPortraitUrl, getGameAssetUrl, withBasePublicPath } from '@/utils/assetUrls'

describe('assetUrls', () => {
  it('prefixes public assets with the Vite base URL', () => {
    expect(withBasePublicPath('icons/edit.png')).toBe('/icons/edit.png')
    expect(withBasePublicPath('/sfx/click.ogg')).toBe('/sfx/click.ogg')
  })

  it('keeps game assets on the backend /assets route', () => {
    expect(getGameAssetUrl('tiles/plain.png')).toBe('/assets/tiles/plain.png')
    expect(getGameAssetUrl('/males/1.png')).toBe('/assets/males/1.png')
  })

  it('builds avatar portrait urls from gender and pic id', () => {
    expect(getAvatarPortraitUrl('male', 3)).toBe('/assets/males/3.png')
    expect(getAvatarPortraitUrl('female', 8)).toBe('/assets/females/8.png')
    expect(getAvatarPortraitUrl('女', 5)).toBe('/assets/females/5.png')
    expect(getAvatarPortraitUrl('male', null)).toBe('')
  })
})
