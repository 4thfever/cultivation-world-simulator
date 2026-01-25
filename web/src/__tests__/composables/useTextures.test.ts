import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Use vi.hoisted to define mocks before vi.mock is hoisted.
const { mockAssetsLoad, mockFetchAvatarMeta, mockGetClusteredTileVariant } = vi.hoisted(() => ({
  mockAssetsLoad: vi.fn().mockResolvedValue({ valid: true }),
  mockFetchAvatarMeta: vi.fn(),
  mockGetClusteredTileVariant: vi.fn((x: number, y: number, count: number) => (x + y) % count),
}))

// Mock pixi.js.
vi.mock('pixi.js', () => ({
  Assets: {
    load: mockAssetsLoad,
  },
  Texture: {},
  TextureStyle: {
    defaultOptions: {
      scaleMode: 'linear',
    },
  },
}))

// Mock avatar API.
vi.mock('@/api', () => ({
  avatarApi: {
    fetchAvatarMeta: mockFetchAvatarMeta,
  },
}))

// Mock procedural utils.
vi.mock('@/utils/procedural', () => ({
  getClusteredTileVariant: mockGetClusteredTileVariant,
}))

import { useTextures } from '@/components/game/composables/useTextures'

describe('useTextures', () => {
  // Get references to shared state for resetting between tests.
  let texturesInstance: ReturnType<typeof useTextures>

  beforeEach(() => {
    vi.clearAllMocks()
    mockAssetsLoad.mockResolvedValue({ valid: true })

    // Get instance and reset shared state.
    texturesInstance = useTextures()

    // Clear all textures to force reload.
    Object.keys(texturesInstance.textures.value).forEach(key => {
      delete texturesInstance.textures.value[key]
    })

    // Reset isLoaded to false to allow reloading.
    texturesInstance.isLoaded.value = false

    // Reset available avatars.
    texturesInstance.availableAvatars.value = { males: [], females: [] }
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('return values', () => {
    it('should return textures ref', () => {
      const { textures } = useTextures()
      expect(textures).toBeDefined()
      expect(textures.value).toBeDefined()
    })

    it('should return isLoaded ref', () => {
      const { isLoaded } = useTextures()
      expect(isLoaded).toBeDefined()
    })

    it('should return availableAvatars ref', () => {
      const { availableAvatars } = useTextures()
      expect(availableAvatars).toBeDefined()
      expect(availableAvatars.value).toHaveProperty('males')
      expect(availableAvatars.value).toHaveProperty('females')
    })

    it('should return loadBaseTextures function', () => {
      const { loadBaseTextures } = useTextures()
      expect(typeof loadBaseTextures).toBe('function')
    })

    it('should return loadSectTexture function', () => {
      const { loadSectTexture } = useTextures()
      expect(typeof loadSectTexture).toBe('function')
    })

    it('should return loadCityTexture function', () => {
      const { loadCityTexture } = useTextures()
      expect(typeof loadCityTexture).toBe('function')
    })

    it('should return getTileTexture function', () => {
      const { getTileTexture } = useTextures()
      expect(typeof getTileTexture).toBe('function')
    })
  })

  describe('loadBaseTextures', () => {
    it('should fetch avatar meta', async () => {
      mockFetchAvatarMeta.mockResolvedValue({
        males: [1, 2, 3],
        females: [1, 2],
      })

      const { loadBaseTextures } = useTextures()
      await loadBaseTextures()

      expect(mockFetchAvatarMeta).toHaveBeenCalled()
    })

    it('should load base tile textures', async () => {
      mockFetchAvatarMeta.mockResolvedValue({
        males: [],
        females: [],
      })

      const { loadBaseTextures } = useTextures()
      await loadBaseTextures()

      // Should load various tile textures.
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/tiles/plain.png')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/tiles/water.png')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/tiles/city.png')
    })

    it('should load tile variants', async () => {
      mockFetchAvatarMeta.mockResolvedValue({
        males: [],
        females: [],
      })

      const { loadBaseTextures } = useTextures()
      await loadBaseTextures()

      // Should load variant textures (e.g., forest_0, forest_1, etc.).
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/tiles/forest_0.png')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/tiles/mountain_0.png')
    })

    it('should load cloud textures', async () => {
      mockFetchAvatarMeta.mockResolvedValue({
        males: [],
        females: [],
      })

      const { loadBaseTextures } = useTextures()
      await loadBaseTextures()

      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/clouds/cloud_0.png')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/clouds/cloud_8.png')
    })

    it('should load avatar textures based on meta', async () => {
      mockFetchAvatarMeta.mockResolvedValue({
        males: [1, 5, 10],
        females: [2, 7],
      })

      const { loadBaseTextures } = useTextures()
      await loadBaseTextures()

      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/males/1.png')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/males/5.png')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/males/10.png')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/females/2.png')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/females/7.png')
    })

    it('should use fallback avatar range when meta fetch fails', async () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      mockFetchAvatarMeta.mockRejectedValue(new Error('Network error'))

      const { loadBaseTextures, availableAvatars } = useTextures()
      await loadBaseTextures()

      // Should use fallback range.
      expect(availableAvatars.value.males.length).toBe(47)
      expect(availableAvatars.value.females.length).toBe(41)

      consoleSpy.mockRestore()
    })

    it('should set isLoaded to true after loading', async () => {
      mockFetchAvatarMeta.mockResolvedValue({
        males: [],
        females: [],
      })

      const { loadBaseTextures, isLoaded } = useTextures()
      await loadBaseTextures()

      expect(isLoaded.value).toBe(true)
    })

    it('should handle individual texture load failures gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockFetchAvatarMeta.mockResolvedValue({
        males: [],
        females: [],
      })
      mockAssetsLoad.mockImplementation((url: string) => {
        if (url.includes('plain')) {
          return Promise.reject(new Error('Load failed'))
        }
        return Promise.resolve({ valid: true })
      })

      const { loadBaseTextures, isLoaded } = useTextures()
      await loadBaseTextures()

      // Should still complete and set isLoaded.
      expect(isLoaded.value).toBe(true)

      consoleSpy.mockRestore()
    })
  })

  describe('loadSectTexture', () => {
    it('should load 4 sect texture slices', async () => {
      const { loadSectTexture, textures } = useTextures()

      // Clear any existing sect textures.
      delete textures.value['sect_1_0']
      delete textures.value['sect_1_1']
      delete textures.value['sect_1_2']
      delete textures.value['sect_1_3']

      await loadSectTexture(1)

      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/sects/sect_1_0.png')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/sects/sect_1_1.png')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/sects/sect_1_2.png')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/sects/sect_1_3.png')
    })

    it('should store sect textures in cache', async () => {
      const { loadSectTexture, textures } = useTextures()

      await loadSectTexture(5)

      expect(textures.value['sect_5_0']).toBeDefined()
      expect(textures.value['sect_5_1']).toBeDefined()
      expect(textures.value['sect_5_2']).toBeDefined()
      expect(textures.value['sect_5_3']).toBeDefined()
    })

    it('should not reload already cached textures', async () => {
      const { loadSectTexture, textures } = useTextures()

      // Pre-populate cache.
      textures.value['sect_3_0'] = { valid: true } as any
      textures.value['sect_3_1'] = { valid: true } as any
      textures.value['sect_3_2'] = { valid: true } as any
      textures.value['sect_3_3'] = { valid: true } as any

      vi.clearAllMocks()
      await loadSectTexture(3)

      // Should not call Assets.load for already cached textures.
      expect(mockAssetsLoad).not.toHaveBeenCalled()
    })
  })

  describe('loadCityTexture', () => {
    it('should load 4 city texture slices', async () => {
      const { loadCityTexture } = useTextures()

      await loadCityTexture(2)

      // Should try jpg extension first.
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/cities/city_2_0.jpg')
    })

    it('should store city textures in cache', async () => {
      const { loadCityTexture, textures } = useTextures()

      await loadCityTexture(7)

      expect(textures.value['city_7_0']).toBeDefined()
    })

    it('should try png if jpg fails', async () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      mockAssetsLoad.mockImplementation((url: string) => {
        if (url.endsWith('.jpg')) {
          return Promise.reject(new Error('Not found'))
        }
        return Promise.resolve({ valid: true })
      })

      const { loadCityTexture } = useTextures()

      await loadCityTexture(4)

      // Should have tried png after jpg failed.
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/cities/city_4_0.jpg')
      expect(mockAssetsLoad).toHaveBeenCalledWith('/assets/cities/city_4_0.png')

      consoleSpy.mockRestore()
    })
  })

  describe('getTileTexture', () => {
    it('should return base texture for non-variant types', () => {
      const { getTileTexture, textures } = useTextures()

      const plainTexture = { valid: true, type: 'plain' }
      textures.value['PLAIN'] = plainTexture as any

      const result = getTileTexture('PLAIN', 0, 0)

      // Use toEqual for object comparison.
      expect(result).toEqual(plainTexture)
    })

    it('should return variant texture for variant types', () => {
      const { getTileTexture, textures } = useTextures()

      // Set up variant textures.
      textures.value['FOREST_0'] = { valid: true, variant: 0 } as any
      textures.value['FOREST_1'] = { valid: true, variant: 1 } as any

      // Mock getClusteredTileVariant to return 1.
      mockGetClusteredTileVariant.mockReturnValue(1)

      const result = getTileTexture('FOREST', 5, 5)

      expect(mockGetClusteredTileVariant).toHaveBeenCalledWith(5, 5, 9)
      expect(result).toEqual({ valid: true, variant: 1 })
    })

    it('should fallback to base texture if variant not found', () => {
      const { getTileTexture, textures } = useTextures()

      // Only set base texture, no variants.
      const glacierTexture = { valid: true, type: 'glacier' }
      textures.value['GLACIER'] = glacierTexture as any
      // Clear any variant.
      delete textures.value['GLACIER_5']

      mockGetClusteredTileVariant.mockReturnValue(5)

      const result = getTileTexture('GLACIER', 0, 0)

      expect(result).toEqual(glacierTexture)
    })

    it('should return undefined for unknown texture types', () => {
      const { getTileTexture, textures } = useTextures()

      // Ensure texture doesn't exist.
      delete textures.value['UNKNOWN_TYPE']

      const result = getTileTexture('UNKNOWN_TYPE', 0, 0)

      expect(result).toBeUndefined()
    })
  })

  describe('texture caching', () => {
    it('should share texture cache between composable instances', () => {
      const instance1 = useTextures()
      const instance2 = useTextures()

      instance1.textures.value['shared_test_texture'] = { valid: true } as any

      // Both instances should see the same texture.
      expect(instance2.textures.value['shared_test_texture']).toBeDefined()
    })

    it('should share isLoaded state between instances', () => {
      const instance1 = useTextures()
      const instance2 = useTextures()

      // Both should reference the same isLoaded.
      expect(instance1.isLoaded).toBe(instance2.isLoaded)
    })
  })

  describe('meta change detection', () => {
    it('should detect and update when avatar meta changes', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

      // First call with initial meta.
      mockFetchAvatarMeta.mockResolvedValueOnce({
        males: [1, 2],
        females: [1],
      })

      const { loadBaseTextures, availableAvatars, isLoaded } = useTextures()

      await loadBaseTextures()

      expect(availableAvatars.value.males).toEqual([1, 2])
      expect(availableAvatars.value.females).toEqual([1])

      // Second call with different meta - reset isLoaded first.
      isLoaded.value = false
      mockFetchAvatarMeta.mockResolvedValueOnce({
        males: [1, 2, 3],
        females: [1, 2],
      })

      await loadBaseTextures()

      expect(availableAvatars.value.males).toEqual([1, 2, 3])
      expect(availableAvatars.value.females).toEqual([1, 2])

      consoleSpy.mockRestore()
    })
  })
})
