import { ref } from 'vue'
import { Assets, Texture } from 'pixi.js'

// 全局纹理缓存，避免重复加载
const textures = ref<Record<string, Texture>>({})
const isLoaded = ref(false)

export function useTextures() {
  
  // 基础纹理加载（地图块、角色）
  const loadBaseTextures = async () => {
    if (isLoaded.value) return

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

    // 加载基础地图纹理
    for (const [key, url] of Object.entries(manifest)) {
      try {
        textures.value[key] = await Assets.load(url)
      } catch (e) {
        console.error(`Failed to load texture: ${url}`, e)
      }
    }

    // 加载角色立绘 (1-16)
    for (let i = 1; i <= 16; i++) {
      const maleUrl = `/assets/males/${i}.png`
      const femaleUrl = `/assets/females/${i}.png`

      try {
        textures.value[`male_${i}`] = await Assets.load(maleUrl)
      } catch (e) { /* ignore */ }

      try {
        textures.value[`female_${i}`] = await Assets.load(femaleUrl)
      } catch (e) { /* ignore */ }
    }

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
    loadSectTexture
  }
}

