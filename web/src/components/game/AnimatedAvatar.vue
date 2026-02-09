<script setup lang="ts">
import { useTextures } from './composables/useTextures'
import { ref, watch, computed } from 'vue'
import { Graphics } from 'pixi.js'
import type { AvatarSummary } from '../../types/core'
import { useSharedTicker } from './composables/useSharedTicker'
import { avatarIdToColor } from '../../utils/eventHelper'
import { useAudio } from '../../composables/useAudio'

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
    
    // Emoji bobbing animation
    emojiTime += delta * 0.05
    emojiBob.value = Math.sin(emojiTime) * 5
})

let emojiTime = 0
const emojiBob = ref(0)

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
  // Scale up: 3.5x tile size
  return (props.tileSize * 3.5) / Math.max(tex.width, tex.height)
}

const drawFallback = (g: Graphics) => {
    g.clear()
    g.circle(0, 0, props.tileSize * 0.5)
    g.fill({ color: props.avatar.gender === 'female' ? 0xffaaaa : 0xaaaaff })
    g.stroke({ width: 2, color: 0x000000 })
}

const nameStyle = computed(() => ({
    fontFamily: '"Microsoft YaHei", sans-serif',
    fontSize: 50,
    fontWeight: 'bold',
    fill: avatarIdToColor(props.avatar.id),
    stroke: { color: '#000000', width: 4 },
    align: 'center',
    dropShadow: {
        color: '#000000',
        blur: 2,
        angle: Math.PI / 6,
        distance: 2,
        alpha: 0.8
    }
} as any))

function handlePointerTap() {
    useAudio().play('select')
    emit('select', {
        type: 'avatar',
        id: props.avatar.id,
        name: props.avatar.name
    })
}

const emojiStyle = {
    fontFamily: '"Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif',
    fontSize: 70,
    align: 'center',
} as any

const drawEmojiBg = (g: Graphics) => {
    g.clear()
    
    const w = 80
    const h = 80
    const r = 16
    const halfW = w / 2
    const halfH = h / 2
    
    // 1. Draw all fills first (to cover background)
    g.beginPath()
    g.roundRect(-halfW, -halfH, w, h, r)
    g.fill({ color: 0xffffff, alpha: 1.0 })
    
    // Tail fill
    g.beginPath()
    g.moveTo(-halfW + 10, halfH)     // Start at bottom-left area of body
    g.lineTo(-halfW - 10, halfH + 20) // Point pointing down-left
    g.lineTo(-halfW, halfH - 10)      // Back to left edge of body
    g.closePath()
    g.fill({ color: 0xffffff, alpha: 1.0 })

    // 2. Draw Strokes (Outlines)
    // We draw the bubble body stroke
    g.roundRect(-halfW, -halfH, w, h, r)
    g.stroke({ width: 3, color: 0x000000, alpha: 1.0 })
    
    // We draw the tail stroke
    g.beginPath()
    g.moveTo(-halfW + 10, halfH)
    g.lineTo(-halfW - 10, halfH + 20)
    g.lineTo(-halfW, halfH - 10)
    g.stroke({ width: 3, color: 0x000000, alpha: 1.0 })

    // 3. Clean up the intersection with a white patch
    // We fill a small polygon over the line where tail meets body
    g.beginPath()
    g.moveTo(-halfW + 8, halfH - 2)   // Inside body, near bottom
    g.lineTo(-halfW - 2, halfH - 12)  // Inside body, near left
    g.lineTo(-halfW - 8, halfH + 16)  // Towards tail tip (but not all the way)
    g.lineTo(-halfW + 8, halfH + 2)   // Towards tail base
    g.closePath()
    g.fill({ color: 0xffffff, alpha: 1.0 })
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

    <!-- Emoji Bubble -->
    <container
      v-if="avatar.action_emoji"
      :x="tileSize * 0.6"
      :y="(getTexture() ? -tileSize * 3.5 : -tileSize * 1.2) + emojiBob"
      :z-index="100"
    >
        <graphics @render="drawEmojiBg" />
        <text
            :text="avatar.action_emoji"
            :style="emojiStyle"
            :anchor="0.5"
            :scale="1.0"
        />
    </container>

    <text
      :text="avatar.name"
      :style="nameStyle"
      :anchor-x="0.5"
      :anchor-y="0"
      :y="10"
    />
  </container>
</template>
