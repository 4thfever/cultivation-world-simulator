import { markRaw, ref, shallowRef } from 'vue'
import { Assets, Texture, TextureStyle } from 'pixi.js'
import { avatarApi } from '@/api'
import type { RegionSummary } from '@/types/core'
import { getClusteredTileVariant } from '@/utils/procedural'
import { logError, logWarn } from '@/utils/appError'
import { getAvatarIndexSlug, getAvatarPortraitUrl, getRealmAssetSlug, getGameAssetUrl } from '@/utils/assetUrls'

// 设置全局纹理缩放模式为 nearest (像素风)
TextureStyle.defaultOptions.scaleMode = 'nearest'

// 地形变体配置
// startIndex: 变体索引起始值，默认为 0
const TILE_VARIANTS: Record<string, { prefix: string, count: number, startIndex?: number }> = {
  // 从 0 开始的变体 (0-8)
  'GLACIER': { prefix: 'glacier', count: 9, startIndex: 0 },
  'MOUNTAIN': { prefix: 'mountain', count: 9, startIndex: 0 },
  'DESERT': { prefix: 'desert', count: 9, startIndex: 0 }, 
  'SNOW_MOUNTAIN': { prefix: 'snow_mountain', count: 9, startIndex: 0 },
  'FOREST': { prefix: 'forest', count: 9, startIndex: 0 },
  'GRASSLAND': { prefix: 'grassland', count: 9, startIndex: 0 },
  'RAINFOREST': { prefix: 'rainforest', count: 9, startIndex: 0 },
  'BAMBOO': { prefix: 'bamboo', count: 9, startIndex: 0 },
  'GOBI': { prefix: 'gobi', count: 9, startIndex: 0 },
  'ISLAND': { prefix: 'island', count: 9, startIndex: 0 },
  'SWAMP': { prefix: 'swamp', count: 9, startIndex: 0 },
}

// 全局纹理缓存，避免重复加载。Pixi Texture 不能进入 Vue 深层响应式代理。
const textures = shallowRef<Record<string, Texture>>({})
const isLoaded = ref(false)
const availableAvatars = ref<{ males: number[], females: number[] }>({ males: [], females: [] })
let baseTexturesPromise: Promise<void> | null = null
const sectTexturePromises = new Map<number, Promise<void>>()
const cityTexturePromises = new Map<number, Promise<void>>()
const avatarTexturePromises = new Map<string, Promise<void>>()

function setTexture(key: string, texture: Texture) {
  textures.value[key] = markRaw(texture)
}

function getAvatarTextureKey(gender: string | undefined, picId: number | null | undefined, realm: string | null | undefined): string {
  const normalizedGender = String(gender || '').toLowerCase() === 'female' ? 'female' : 'male'
  return `${normalizedGender}_${getAvatarIndexSlug(picId)}_${getRealmAssetSlug(realm)}`
}

export function useTextures() {
  
  // 基础纹理加载（地图块、角色）
  const loadBaseTextures = async () => {
    if (baseTexturesPromise) return baseTexturesPromise

    baseTexturesPromise = (async () => {
    // 1. 获取最新的 Avatar Meta 并检查是否有变化
    let metaChanged = false
    try {
        const meta = await avatarApi.fetchAvatarMeta()
        
        // 对比当前缓存的列表和新获取的列表
        const newMalesStr = JSON.stringify(meta.males || [])
        const curMalesStr = JSON.stringify(availableAvatars.value.males)
        if (meta.males && newMalesStr !== curMalesStr) {
            availableAvatars.value.males = meta.males
            metaChanged = true
        }

        const newFemalesStr = JSON.stringify(meta.females || [])
        const curFemalesStr = JSON.stringify(availableAvatars.value.females)
        if (meta.females && newFemalesStr !== curFemalesStr) {
            availableAvatars.value.females = meta.females
            metaChanged = true
        }
        
    } catch (e) {
        logWarn('Textures load avatar meta', e)
        // Fallback: 只有在列表为空时才使用默认值
        if (availableAvatars.value.males.length === 0) {
            availableAvatars.value.males = Array.from({length: 48}, (_, i) => i + 1)
            availableAvatars.value.females = Array.from({length: 48}, (_, i) => i + 1)
            metaChanged = true
        }
    }

    // 2. 如果已经加载过，且元数据没有变化，则跳过
    // 注意：如果 metaChanged 为 true，即使 isLoaded 为 true 也要重新执行加载逻辑（Pixi Assets 会处理去重）
    if (isLoaded.value && !metaChanged) {
        return
    }

    const manifest: Record<string, string> = {
      'PLAIN': getGameAssetUrl('tiles/plain.png'),
      'WATER': getGameAssetUrl('tiles/water.png'),
      'SEA': getGameAssetUrl('tiles/sea.png'),
      'WATER_FULL': getGameAssetUrl('tiles/water_full.jpg'),
      'SEA_FULL': getGameAssetUrl('tiles/sea_full.jpg'),
      'CITY': getGameAssetUrl('tiles/city.png'),
      'VOLCANO': getGameAssetUrl('tiles/volcano.png'),
      'SWAMP': getGameAssetUrl('tiles/swamp.png'),
      'FARM': getGameAssetUrl('tiles/farm.png'),
      'ISLAND': getGameAssetUrl('tiles/island.png'),
      'BAMBOO': getGameAssetUrl('tiles/bamboo.png'),
      'GOBI': getGameAssetUrl('tiles/gobi.png'),
      'TUNDRA': getGameAssetUrl('tiles/tundra.png'),
      'MARSH': getGameAssetUrl('tiles/swamp.png'),
      // Cave slices
      'cave_0': getGameAssetUrl('tiles/cave_0.png'),
      'cave_1': getGameAssetUrl('tiles/cave_1.png'),
      'cave_2': getGameAssetUrl('tiles/cave_2.png'),
      'cave_3': getGameAssetUrl('tiles/cave_3.png'),
      // Ruin slices
      'ruin_0': getGameAssetUrl('tiles/ruin_0.png'),
      'ruin_1': getGameAssetUrl('tiles/ruin_1.png'),
      'ruin_2': getGameAssetUrl('tiles/ruin_2.png'),
      'ruin_3': getGameAssetUrl('tiles/ruin_3.png'),
    }

    const tilePromises = Object.entries(manifest).map(async ([key, url]) => {
      try {
        setTexture(key, await Assets.load(url))
      } catch (error) {
        logError(`Textures load base texture ${key}`, error)
      }
    })

    // Load Tile Variants
    const variantPromises: Promise<void>[] = []
    Object.entries(TILE_VARIANTS).forEach(([key, { prefix, count, startIndex = 0 }]) => {
      for (let i = startIndex; i < startIndex + count; i++) {
        const variantKey = `${key}_${i}`
        const url = getGameAssetUrl(`tiles/${prefix}_${i}.png`)
        variantPromises.push(
          Assets.load(url)
            .then(tex => { setTexture(variantKey, tex) })
            .catch(e => logWarn(`Textures load variant ${variantKey}`, e))
        )
      }
    })

    // Load Clouds
    const cloudPromises: Promise<void>[] = []
    for (let i = 0; i <= 8; i++) {
        cloudPromises.push(
            Assets.load(getGameAssetUrl(`clouds/cloud_${i}.png`))
                .then(tex => { setTexture(`cloud_${i}`, tex) })
                .catch(e => logWarn(`Textures load cloud_${i}`, e))
        )
    }

    await Promise.all([...tilePromises, ...variantPromises, ...cloudPromises])

    // 为没有基础纹理的变体类型设置默认纹理（使用第0个变体作为默认值）
    Object.keys(TILE_VARIANTS).forEach(key => {
        if (!textures.value[key] && textures.value[`${key}_0`]) {
            setTexture(key, textures.value[`${key}_0`])
        }
    })

    isLoaded.value = true
    })().finally(() => {
      baseTexturesPromise = null
    })

    return baseTexturesPromise
  }

  // 动态加载宗门纹理（按需）- 加载4个切片用于渲染
  const loadSectTexture = async (sectId: number) => {
      if ([0, 1, 2, 3].every(i => textures.value[`sect_${sectId}_${i}`])) return
      const existingPromise = sectTexturePromises.get(sectId)
      if (existingPromise) return existingPromise

      // 加载4个切片 _0, _1, _2, _3
      const slicePromises = [0, 1, 2, 3].map(async (i) => {
          const key = `sect_${sectId}_${i}`
          if (textures.value[key]) return
          
          const url = getGameAssetUrl(`sects/sect_${sectId}_${i}.png`)
          try {
              const tex = await Assets.load(url)
              setTexture(key, tex)
          } catch (e) {
              logWarn(`Textures load sect_${sectId}_${i}`, e)
          }
      })
      
      const promise = Promise.all(slicePromises)
        .then(() => undefined)
        .finally(() => {
          sectTexturePromises.delete(sectId)
        })
      sectTexturePromises.set(sectId, promise)
      return promise
  }

  // 动态加载城市纹理（按需）- 加载4个切片用于渲染
  const loadCityTexture = async (cityId: number) => {
      if ([0, 1, 2, 3].every(i => textures.value[`city_${cityId}_${i}`])) return
      const existingPromise = cityTexturePromises.get(cityId)
      if (existingPromise) return existingPromise

      // 加载4个切片 _0, _1, _2, _3
      const extensions = ['.jpg', '.png']
      
      const slicePromises = [0, 1, 2, 3].map(async (i) => {
          const key = `city_${cityId}_${i}`
          if (textures.value[key]) return
          
          for (const ext of extensions) {
              const url = getGameAssetUrl(`cities/city_${cityId}_${i}${ext}`)
              try {
                  const tex = await Assets.load(url)
                  setTexture(key, tex)
                  return
              } catch (e) {
                  logWarn(`Textures load city_${cityId}_${i}${ext}`, e)
              }
          }
      })
      
      const promise = Promise.all(slicePromises)
        .then(() => undefined)
        .finally(() => {
          cityTexturePromises.delete(cityId)
        })
      cityTexturePromises.set(cityId, promise)
      return promise
  }

  const preloadRegionTextures = async (regions: Iterable<RegionSummary>) => {
      const regionList = Array.from(regions)
      const sectIds = Array.from(
        new Set(
          regionList
            .filter(region => region.type === 'sect' && region.sect_id)
            .map(region => region.sect_id as number)
        )
      )

      const cityIds = Array.from(
        new Set(
          regionList
            .filter(region => region.type === 'city' && region.id)
            .map(region => {
              const id = typeof region.id === 'string' ? parseInt(region.id) : region.id
              return isNaN(id) ? null : id
            })
            .filter(id => id !== null)
        )
      ) as number[]

      await Promise.all([
        ...sectIds.map(id => loadSectTexture(id)),
        ...cityIds.map(id => loadCityTexture(id))
      ])
  }

  const ensureAvatarTexture = (
    gender: string | undefined,
    picId: number | null | undefined,
    realm: string | null | undefined,
  ): Texture | undefined => {
    if (!picId) return undefined
    const key = getAvatarTextureKey(gender, picId, realm)
    if (textures.value[key]) return textures.value[key]
    if (avatarTexturePromises.has(key)) return undefined

    const promise = Assets.load(getAvatarPortraitUrl(gender, picId, realm))
      .then(tex => { setTexture(key, tex) })
      .catch(e => logWarn(`Textures load avatar ${key}`, e))
      .finally(() => {
        avatarTexturePromises.delete(key)
      })
    avatarTexturePromises.set(key, promise)
    return undefined
  }

  // 获取地形纹理（支持随机变体）
  const getTileTexture = (type: string, x: number, y: number): Texture | undefined => {
    const variantConfig = TILE_VARIANTS[type]
    if (variantConfig) {
      // 使用噪声聚类算法替代纯随机 Hash
      // 让变体在地图上呈现自然的群落分布，减少视觉噪点
      const index = getClusteredTileVariant(x, y, variantConfig.count)
      const variantKey = `${type}_${index}`
      
      if (textures.value[variantKey]) {
        return textures.value[variantKey]
      }
    }
    return textures.value[type]
  }

  return {
    textures,
    isLoaded,
    loadBaseTextures,
    loadSectTexture,
    loadCityTexture,
    preloadRegionTextures,
    availableAvatars,
    ensureAvatarTexture,
    getTileTexture
  }
}

