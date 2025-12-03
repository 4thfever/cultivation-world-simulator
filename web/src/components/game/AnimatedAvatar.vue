<script setup lang="ts">
import { useTextures } from './composables/useTextures'
import { ref, watch } from 'vue'
import { Graphics } from 'pixi.js'
import type { AvatarSummary } from '../../types/core'
import { useSharedTicker } from './composables/useSharedTicker'

const props = defineProps<{
  avatar: AvatarSummary
  tileSize: number
  offset?: { x: number; y: number }
}>()

const emit = defineEmits<{
  (e: 'select', payload: { type: 'avatar'; id: string; name?: string }): void
}>()

const { textures, availableAvatars } = useTextures()

// Target position (grid coordinates)
const targetX = ref(props.avatar.x)
const targetY = ref(props.avatar.y)

// Current render position (pixel coordinates)
// Initial position includes offset immediately to avoid "jumping" on spawn if possible,
// but props.offset might be undefined initially.
const initialOffsetX = props.offset?.x ?? 0
const initialOffsetY = props.offset?.y ?? 0
const currentX = ref((props.avatar.x + initialOffsetX) * props.tileSize + props.tileSize / 2)
const currentY = ref((props.avatar.y + initialOffsetY) * props.tileSize + props.tileSize / 2)

// Watch for prop updates (server ticks)
watch(() => [props.avatar.x, props.avatar.y], ([newX, newY]) => {
    targetX.value = newX
    targetY.value = newY
})

useSharedTicker((delta) => {
    const offsetX = props.offset?.x ?? 0
    const offsetY = props.offset?.y ?? 0
    
    const destX = (targetX.value + offsetX) * props.tileSize + props.tileSize / 2
    const destY = (targetY.value + offsetY) * props.tileSize + props.tileSize / 2
    
    const speed = 0.1 * delta
    
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

function getTexture() {
  const gender = (props.avatar.gender || 'male').toLowerCase()
  let pid = props.avatar.pic_id
  
  // Fallback logic if pic_id is missing
  if (!pid) {
     const list = availableAvatars.value[gender === 'female' ? 'females' : 'males']
     if (list && list.length > 0) {
         let hash = 0
         const str = props.avatar.id || props.avatar.name || 'default'
         for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash)
         }
         pid = list[Math.abs(hash) % list.length]
     } else {
         pid = 1
     }
  }

  const key = `${gender}_${pid}`
  return textures.value[key]
}

function getScale() {
  const tex = getTexture()
  if (!tex) return 1
  // Scale up: 3.0x tile size
  return (props.tileSize * 3.0) / Math.max(tex.width, tex.height)
}

const drawFallback = (g: Graphics) => {
    g.clear()
    g.circle(0, 0, props.tileSize * 0.5)
    g.fill({ color: props.avatar.gender === 'female' ? 0xffaaaa : 0xaaaaff })
    g.stroke({ width: 2, color: 0x000000 })
}

const nameStyle = {
    fontFamily: '"Microsoft YaHei", sans-serif',
    fontSize: 42,
    fontWeight: 'bold',
    fill: '#ffffff',
    stroke: { color: '#000000', width: 3.5 },
    align: 'center',
    dropShadow: {
        color: '#000000',
        blur: 2,
        angle: Math.PI / 6,
        distance: 2,
        alpha: 0.8
    }
} as any

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
