<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Container, Sprite, Ticker } from 'pixi.js'
import { useTextures } from './composables/useTextures'
import { useWorldStore } from '../../stores/world'

const props = defineProps<{
  width: number
  height: number
}>()

const { textures } = useTextures()
const worldStore = useWorldStore()
const container = ref<Container>()

interface Cloud {
  sprite: Sprite
  shadow: Sprite
  speedX: number
  speedY: number
}

const activeClouds = ref<Cloud[]>([])
let ticker: Ticker | null = null

// Config mappings
const MAX_CLOUDS = {
  'none': 0,
  'low': 1,
  'high': 5
}
const SPAWN_CHANCE = 0.01 // 稍微提高生成检测频率，因为有最大数量限制

function getCloudFreq() {
  const freq = worldStore.frontendConfig.cloud_freq || 'none'
  return freq as keyof typeof MAX_CLOUDS
}

/**
 * Spawn a single cloud
 * @param initial If true, spawn anywhere on screen. If false, spawn off-screen (left).
 */
function spawnCloud(initial: boolean = false) {
  const freq = getCloudFreq()
  const max = MAX_CLOUDS[freq] || 0
  
  if (activeClouds.value.length >= max) return

  // 1. Pick random texture
  const cloudIdx = Math.floor(Math.random() * 9) // 0-8
  const tex = textures.value[`cloud_${cloudIdx}`]
  if (!tex) return

  // 2. Create Cloud Sprite
  const sprite = new Sprite(tex)
  sprite.anchor.set(0.5)
  
  // Scale
  const scale = 2.0 + Math.random() * 2.0 // 2.0 - 4.0
  sprite.scale.set(scale)
  
  // Alpha & Tint (More transparent, slightly white/blueish)
  sprite.alpha = 0.55 + Math.random() * 0.15 // 0.55 - 0.7
  
  // 3. Create Shadow Sprite (For height effect)
  const shadow = new Sprite(tex)
  shadow.anchor.set(0.5)
  shadow.scale.set(scale) // Same scale
  shadow.tint = 0x000000  // Black
  shadow.alpha = 0.3      // Faint shadow
  
  // 4. Determine Position & Speed
  // Main wind direction: Left to Right (West to East)
  const speedX = 0.3 + Math.random() * 0.4  // 0.3 - 0.7
  const speedY = (Math.random() - 0.5) * 0.1 // Slight vertical drift
  
  let x, y
  const margin = 200
  
  if (initial) {
    // Random anywhere
    x = Math.random() * props.width
    y = Math.random() * props.height
  } else {
    // Start from Left (off-screen)
    x = -margin - Math.random() * 100
    y = Math.random() * props.height
  }
  
  // Apply position
  sprite.x = x
  sprite.y = y
  
  // Shadow offset (simulate height)
  // Higher offset = Higher altitude perception
  // With larger scale, we need larger offset to maintain the "height" illusion relative to cloud size
  const shadowOffsetX = 40 * scale
  const shadowOffsetY = 60 * scale
  
  shadow.x = x + shadowOffsetX
  shadow.y = y + shadowOffsetY

  if (container.value) {
    // Add shadow first so it's below the cloud
    container.value.addChild(shadow)
    container.value.addChild(sprite)
    activeClouds.value.push({ sprite, shadow, speedX, speedY })
  }
}

function updateClouds(dt: number) {
  const bounds = { w: props.width, h: props.height }
  const margin = 300 // Wider margin for cleanup
  
  for (let i = activeClouds.value.length - 1; i >= 0; i--) {
    const cloud = activeClouds.value[i]
    
    // Move Cloud
    cloud.sprite.x += cloud.speedX * dt
    cloud.sprite.y += cloud.speedY * dt
    
    // Move Shadow (Keep offset)
    // Re-calculate offset based on scale to keep it simple, or just apply delta
    cloud.shadow.x += cloud.speedX * dt
    cloud.shadow.y += cloud.speedY * dt
    
    // Boundary Check (Only check Right side since we move Right)
    if (cloud.sprite.x > bounds.w + margin || 
        cloud.sprite.y > bounds.h + margin || 
        cloud.sprite.y < -margin) {
          
      // Remove
      if (container.value) {
        container.value.removeChild(cloud.sprite)
        container.value.removeChild(cloud.shadow)
      }
      activeClouds.value.splice(i, 1)
    }
  }

  // Try spawn
  if (Math.random() < SPAWN_CHANCE) {
    spawnCloud(false) // Spawn from edge
  }
}

function startTicker() {
  if (ticker) return
  ticker = new Ticker()
  ticker.add((t) => updateClouds(t.deltaTime))
  ticker.start()
  
  // Initial population if empty
  if (activeClouds.value.length === 0) {
    const freq = getCloudFreq()
    const max = MAX_CLOUDS[freq] || 0
    // Spawn a few initial clouds randomly placed
    for (let i = 0; i < max; i++) {
       spawnCloud(true)
    }
  }
}

function stopTicker() {
  if (ticker) {
    ticker.stop()
    ticker.destroy()
    ticker = null
  }
}

function clearClouds() {
  if (container.value) {
    container.value.removeChildren()
  }
  activeClouds.value = []
}

watch(() => worldStore.frontendConfig.cloud_freq, (val) => {
  const freq = val || 'none'
  if (freq === 'none') {
    clearClouds()
    stopTicker()
  } else {
    startTicker()
  }
}, { immediate: true })

onMounted(() => {
  if (getCloudFreq() !== 'none') {
    startTicker()
  }
})

onUnmounted(() => {
  stopTicker()
})

</script>

<template>
  <!-- z-index 300 should be above entities (usually < 100) and map -->
  <container ref="container" :z-index="300" />
</template>
