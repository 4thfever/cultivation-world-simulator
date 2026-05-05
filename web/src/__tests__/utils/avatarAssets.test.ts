import { describe, expect, it } from 'vitest'
import { getAvatarAssetIds, normalizeAvatarAssetLibraries } from '@/utils/avatarAssets'

describe('avatarAssets', () => {
  it('normalizes race-aware libraries', () => {
    const libraries = normalizeAvatarAssetLibraries({
      human: { male: [1], female: [2] },
      fox: { male: [3], female: [4] },
    })

    expect(libraries.human.male).toEqual([1])
    expect(libraries.males).toEqual([1])
    expect(getAvatarAssetIds(libraries, 'fox', '男')).toEqual([3])
    expect(getAvatarAssetIds(libraries, 'fox', 'female')).toEqual([4])
  })

  it('normalizes wrapped and legacy libraries', () => {
    expect(normalizeAvatarAssetLibraries({ data: { human: { male: [1], female: [2] } } }).human.female).toEqual([2])
    expect(normalizeAvatarAssetLibraries({ males: [7], females: [8] }).human).toEqual({ male: [7], female: [8] })
  })
})
