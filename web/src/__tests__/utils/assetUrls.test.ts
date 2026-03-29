import { describe, expect, it } from 'vitest'
import { getGameAssetUrl, withBasePublicPath } from '@/utils/assetUrls'

describe('assetUrls', () => {
  it('prefixes public assets with the Vite base URL', () => {
    expect(withBasePublicPath('icons/edit.png')).toBe('/icons/edit.png')
    expect(withBasePublicPath('/sfx/click.ogg')).toBe('/sfx/click.ogg')
  })

  it('keeps game assets on the backend /assets route', () => {
    expect(getGameAssetUrl('tiles/plain.png')).toBe('/assets/tiles/plain.png')
    expect(getGameAssetUrl('/males/1.png')).toBe('/assets/males/1.png')
  })
})
