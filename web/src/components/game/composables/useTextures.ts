import { ref } from 'vue'
import { Assets, Texture, TextureStyle } from 'pixi.js'
import { gameApi } from '@/api/game'

// 设置全局纹理缩放模式为 nearest (像素风)
TextureStyle.defaultOptions.scaleMode = 'nearest'

// 全局纹理缓存，避免重复加载
const textures = ref<Record<string, Texture>>({})
const isLoaded = ref(false)
const availableAvatars = ref<{ males: number[], females: number[] }>({ males: [], females: [] })

export function useTextures() {
  
  // 基础纹理加载（地图块、角色）
  const loadBaseTextures = async () => {
    if (isLoaded.value) return

    // Load Avatar Meta first
    try {
        const meta = await gameApi.fetchAvatarMeta()
        if (meta.males) availableAvatars.value.males = meta.males
        if (meta.females) availableAvatars.value.females = meta.females
        console.log('Avatar meta loaded:', availableAvatars.value)
    } catch (e) {
        console.warn('Failed to load avatar meta, using default range', e)
        // Fallback
        availableAvatars.value.males = Array.from({length: 47}, (_, i) => i + 1)
        availableAvatars.value.females = Array.from({length: 41}, (_, i) => i + 1)
    }

    const manifest: Record<string, string> = {
      'PLAIN': '/assets/tiles/plain.png',
      'WATER': '/assets/tiles/water.png',
      'SEA': '/assets/tiles/sea.png',
      'WATER_FULL': '/assets/tiles/water_full.jpg',
      'SEA_FULL': '/assets/tiles/sea_full.jpg',
      'MOUNTAIN': '/assets/tiles/mountain.png',
      'FOREST': '/assets/tiles/forest.png',
      'CITY': '/assets/tiles/city.png',
      'DESERT': '/assets/tiles/desert.png',
      'RAINFOREST': '/assets/tiles/rainforest.png',
      'GLACIER': '/assets/tiles/glacier.png',
      'SNOW_MOUNTAIN': '/assets/tiles/snow_mountain.png',
      'VOLCANO': '/assets/tiles/volcano.png',
      'GRASSLAND': '/assets/tiles/grassland.png',
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

    await Promise.all([...tilePromises, ...avatarPromises])

    isLoaded.value = true
    console.log('Base textures loaded')
  }

  // 动态加载宗门纹理（按需）- 加载4个切片用于渲染
  const loadSectTexture = async (sectName: string) => {
      // 加载4个切片 _0, _1, _2, _3
      const slicePromises = [0, 1, 2, 3].map(async (i) => {
          const key = `${sectName}_${i}`
          if (textures.value[key]) return
          
          const url = `/assets/sects/${sectName}_${i}.png`
          try {
              const tex = await Assets.load(url)
              textures.value[key] = tex
          } catch (e) {
              try {
                  const encodedUrl = `/assets/sects/${encodeURIComponent(`${sectName}_${i}`)}.png`
                  const tex = await Assets.load(encodedUrl)
                  textures.value[key] = tex
              } catch (e2) {
                  console.warn(`Failed to load sect slice: ${key}`)
              }
          }
      })
      
      await Promise.all(slicePromises)
  }

  // 动态加载城市纹理（按需）- 加载4个切片用于渲染
  const loadCityTexture = async (cityName: string) => {
      // 加载4个切片 _0, _1, _2, _3
      const extensions = ['.jpg', '.png']
      
      const slicePromises = [0, 1, 2, 3].map(async (i) => {
          const key = `${cityName}_${i}`
          if (textures.value[key]) return
          
          for (const ext of extensions) {
              const url = `/assets/cities/${cityName}_${i}${ext}`
              try {
                  const tex = await Assets.load(url)
                  textures.value[key] = tex
                  return
              } catch (e) {
                  try {
                      const encodedUrl = `/assets/cities/${encodeURIComponent(`${cityName}_${i}`)}${ext}`
                      const tex = await Assets.load(encodedUrl)
                      textures.value[key] = tex
                      return
                  } catch (e2) {
                      // continue
                  }
              }
          }
      })
      
      await Promise.all(slicePromises)
  }

  return {
    textures,
    isLoaded,
    loadBaseTextures,
    loadSectTexture,
    loadCityTexture,
    availableAvatars
  }
}

