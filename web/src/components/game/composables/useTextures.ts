import { ref } from 'vue'
import { Assets, Texture } from 'pixi.js'

// 全局纹理缓存，避免重复加载
const textures = ref<Record<string, Texture>>({})
const isLoaded = ref(false)

export function useTextures() {
  const loadTextures = async () => {
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

    // 加载地图纹理
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
    console.log('Textures loaded')
  }

  return {
    textures,
    isLoaded,
    loadTextures
  }
}

