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
      'CAVE': '/assets/tiles/cave.png',
      'RUINS': '/assets/tiles/ruins.png',
      'FARM': '/assets/tiles/farm.png'
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

  // 动态加载宗门纹理（按需）
  const loadSectTexture = async (sectName: string) => {
      const key = `SECT_${sectName}`
      if (textures.value[key]) return // 已经加载过

      // 假设图片路径规则：/assets/sects/宗门名.png
      // 优先尝试 .png，如果需要支持 .jpg 可能需要额外逻辑，这里先定死 .png
      const url = `/assets/sects/${sectName}.png`
      try {
          const tex = await Assets.load(url)
          textures.value[key] = tex
          console.log(`Loaded sect texture: ${sectName}`)
      } catch (e) {
          console.warn(`Failed to load sect texture for ${sectName}, using fallback.`)
          // 加载失败时不占位，MapLayer 会 fallback 到 CITY
      }
  }

  return {
    textures,
    isLoaded,
    loadBaseTextures,
    loadSectTexture,
    availableAvatars
  }
}

