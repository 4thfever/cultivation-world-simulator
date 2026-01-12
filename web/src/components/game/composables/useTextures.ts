import { ref } from 'vue'
import { Assets, Texture, TextureStyle } from 'pixi.js'
import { avatarApi } from '@/api'
import { getClusteredTileVariant } from '@/utils/procedural'

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

// 全局纹理缓存，避免重复加载
const textures = ref<Record<string, Texture>>({})
const isLoaded = ref(false)
const availableAvatars = ref<{ males: number[], females: number[] }>({ males: [], females: [] })

export function useTextures() {
  
  // 基础纹理加载（地图块、角色）
  const loadBaseTextures = async () => {
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
        
        if (metaChanged) {
            console.log('Avatar meta updated:', availableAvatars.value)
        }
    } catch (e) {
        console.warn('Failed to load avatar meta, using default range', e)
        // Fallback: 只有在列表为空时才使用默认值
        if (availableAvatars.value.males.length === 0) {
            availableAvatars.value.males = Array.from({length: 47}, (_, i) => i + 1)
            availableAvatars.value.females = Array.from({length: 41}, (_, i) => i + 1)
            metaChanged = true
        }
    }

    // 2. 如果已经加载过，且元数据没有变化，则跳过
    // 注意：如果 metaChanged 为 true，即使 isLoaded 为 true 也要重新执行加载逻辑（Pixi Assets 会处理去重）
    if (isLoaded.value && !metaChanged) {
        // Double check if textures are actually loaded for current avatars
        // This handles the case where meta didn't change (e.g. was fallback) but textures weren't loaded
        const missingTexture = availableAvatars.value.males.some(id => !textures.value[`male_${id}`])
        if (!missingTexture) return
    }

    const manifest: Record<string, string> = {
      'PLAIN': '/assets/tiles/plain.png',
      'WATER': '/assets/tiles/water.png',
      'SEA': '/assets/tiles/sea.png',
      'WATER_FULL': '/assets/tiles/water_full.jpg',
      'SEA_FULL': '/assets/tiles/sea_full.jpg',
      'CITY': '/assets/tiles/city.png',
      'VOLCANO': '/assets/tiles/volcano.png',
      'SWAMP': '/assets/tiles/swamp.png',
      'FARM': '/assets/tiles/farm.png',
      'ISLAND': '/assets/tiles/island.png',
      'BAMBOO': '/assets/tiles/bamboo.png',
      'GOBI': '/assets/tiles/gobi.png',
      'TUNDRA': '/assets/tiles/tundra.png',
      'MARSH': '/assets/tiles/swamp.png',
      // Cave slices
      'cave_0': '/assets/tiles/cave_0.png',
      'cave_1': '/assets/tiles/cave_1.png',
      'cave_2': '/assets/tiles/cave_2.png',
      'cave_3': '/assets/tiles/cave_3.png',
      // Ruin slices
      'ruin_0': '/assets/tiles/ruin_0.png',
      'ruin_1': '/assets/tiles/ruin_1.png',
      'ruin_2': '/assets/tiles/ruin_2.png',
      'ruin_3': '/assets/tiles/ruin_3.png',
    }

    const tilePromises = Object.entries(manifest).map(async ([key, url]) => {
      try {
        textures.value[key] = await Assets.load(url)
      } catch (error) {
        console.error(`Failed to load texture: ${url}`, error)
      }
    })

    // Load Tile Variants
    const variantPromises: Promise<void>[] = []
    Object.entries(TILE_VARIANTS).forEach(([key, { prefix, count, startIndex = 0 }]) => {
      for (let i = startIndex; i < startIndex + count; i++) {
        const variantKey = `${key}_${i}`
        const url = `/assets/tiles/${prefix}_${i}.png`
        variantPromises.push(
          Assets.load(url)
            .then(tex => { textures.value[variantKey] = tex })
            .catch(e => console.warn(`Failed to load variant ${variantKey}`, e))
        )
      }
    })

    // Load Clouds
    const cloudPromises: Promise<void>[] = []
    for (let i = 0; i <= 8; i++) {
        cloudPromises.push(
            Assets.load(`/assets/clouds/cloud_${i}.png`)
                .then(tex => { textures.value[`cloud_${i}`] = tex })
                .catch(e => console.warn(`Failed cloud_${i}`, e))
        )
    }

    // Load Avatars based on available IDs
    const avatarPromises: Promise<void>[] = []
    
    for (const id of availableAvatars.value.males) {
        avatarPromises.push(
            Assets.load(`/assets/males/${id}.png`)
                .then(tex => { textures.value[`male_${id}`] = tex })
                .catch(e => console.warn(`Failed male_${id}`, e))
        )
    }
    
    for (const id of availableAvatars.value.females) {
        avatarPromises.push(
            Assets.load(`/assets/females/${id}.png`)
                .then(tex => { textures.value[`female_${id}`] = tex })
                .catch(e => console.warn(`Failed female_${id}`, e))
        )
    }

    await Promise.all([...tilePromises, ...variantPromises, ...avatarPromises, ...cloudPromises])

    // 为没有基础纹理的变体类型设置默认纹理（使用第0个变体作为默认值）
    Object.keys(TILE_VARIANTS).forEach(key => {
        if (!textures.value[key] && textures.value[`${key}_0`]) {
            textures.value[key] = textures.value[`${key}_0`]
        }
    })

    isLoaded.value = true
    console.log('Base textures loaded')
  }

  // 动态加载宗门纹理（按需）- 加载4个切片用于渲染
  const loadSectTexture = async (sectId: number) => {
      // 加载4个切片 _0, _1, _2, _3
      const slicePromises = [0, 1, 2, 3].map(async (i) => {
          const key = `sect_${sectId}_${i}`
          if (textures.value[key]) return
          
          const url = `/assets/sects/sect_${sectId}_${i}.png`
          try {
              const tex = await Assets.load(url)
              textures.value[key] = tex
          } catch (e) {
              console.warn(`Failed to load sect texture: ${url}`, e)
          }
      })
      
      await Promise.all(slicePromises)
  }

  // 动态加载城市纹理（按需）- 加载4个切片用于渲染
  const loadCityTexture = async (cityId: number) => {
      // 加载4个切片 _0, _1, _2, _3
      const extensions = ['.jpg', '.png']
      
      const slicePromises = [0, 1, 2, 3].map(async (i) => {
          const key = `city_${cityId}_${i}`
          if (textures.value[key]) return
          
          for (const ext of extensions) {
              const url = `/assets/cities/city_${cityId}_${i}${ext}`
              try {
                  const tex = await Assets.load(url)
                  textures.value[key] = tex
                  return
              } catch (e) {
                  console.warn(`Failed to load city texture: ${url}`)
              }
          }
      })
      
      await Promise.all(slicePromises)
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
    availableAvatars,
    getTileTexture
  }
}

