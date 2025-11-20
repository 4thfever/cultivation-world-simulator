<script setup lang="ts">
import { useTextures } from './composables/useTextures'
import { ref, watch, onMounted } from 'vue'
import { Graphics, Ticker } from 'pixi.js'
import { useApplication } from 'vue3-pixi'

const props = defineProps<{
  avatar: any
  tileSize: number
}>()

const emit = defineEmits<{
  (e: 'select', payload: { type: 'avatar'; id: string; name?: string }): void
}>()

const { textures } = useTextures()
const app = useApplication()

// Target position (grid coordinates)
const targetX = ref(props.avatar.x)
const targetY = ref(props.avatar.y)

// Current render position (pixel coordinates)
const currentX = ref(props.avatar.x * props.tileSize + props.tileSize / 2)
const currentY = ref(props.avatar.y * props.tileSize + props.tileSize / 2)

// Watch for prop updates (server ticks)
watch(() => [props.avatar.x, props.avatar.y], ([newX, newY]) => {
    targetX.value = newX
    targetY.value = newY
})

// Animation Loop
onMounted(() => {
    const ticker = new Ticker()
    ticker.add((delta) => {
        const destX = targetX.value * props.tileSize + props.tileSize / 2
        const destY = targetY.value * props.tileSize + props.tileSize / 2
        
        // Simple Lerp for smoothness
        // Speed factor: 0.1 means it covers 10% of the remaining distance per frame
        const speed = 0.1 * delta.deltaTime 
        
        if (Math.abs(destX - currentX.value) > 1) {
            currentX.value += (destX - currentX.value) * speed
        } else {
            currentX.value = destX
        }
        
        if (Math.abs(destY - currentY.value) > 1) {
            currentY.value += (destY - currentY.value) * speed
        } else {
            currentY.value = destY
        }
    })
    ticker.start()
    
    // Cleanup manually if needed, though Vue unmount should handle parent destruction
    // Ideally we should attach to app.ticker, but local ticker is easier for per-component logic without memory leaks if managed well.
    // Better approach: use onTick from vue3-pixi if available, or just requestAnimationFrame
})

function getTexture() {
  const key = `${(props.avatar.gender || 'male').toLowerCase()}_${props.avatar.pic_id || 1}`
  return textures.value[key]
}

function getScale() {
  const tex = getTexture()
  if (!tex) return 1
  // Scale up: 2.5x tile size (was 1.8x)
  return (props.tileSize * 2.5) / Math.max(tex.width, tex.height)
}

const drawFallback = (g: Graphics) => {
    g.clear()
    g.circle(0, 0, props.tileSize * 0.8) // Increased size
    g.fill({ color: props.avatar.gender === 'female' ? 0xffaaaa : 0xaaaaff })
    g.stroke({ width: 3, color: 0x000000 })
}

const nameStyle = {
    fontFamily: '"Microsoft YaHei", sans-serif',
    fontSize: 42, // Increased from 36
    fontWeight: 'bold',
    fill: 0xffffff,
    stroke: { color: 0x000000, width: 6 }, // Thicker stroke
    align: 'center',
    dropShadow: {
        color: '#000000',
        blur: 2,
        angle: Math.PI / 6,
        distance: 2,
        alpha: 0.8
    }
}

function handlePointerTap() {
    emit('select', {
        type: 'avatar',
        id: props.avatar.id,
        name: props.avatar.name
    })
}
</script>

<template>
  <container 
    :x="currentX" 
    :y="currentY" 
    :z-index="Math.floor(currentY)"
    event-mode="static"
    cursor="pointer"
    @pointertap="handlePointerTap"
  >
    <sprite
      v-if="getTexture()"
      :texture="getTexture()"
      :anchor-x="0.5"
      :anchor-y="0.9" 
      :scale="getScale()"
    />
    
    <graphics
      v-else
      @render="drawFallback"
    />

    <text
      :text="avatar.name"
      :style="nameStyle"
      :anchor-x="0.5"
      :anchor-y="0"
      :y="10"
    />
  </container>
</template>
