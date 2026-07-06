<script setup lang="ts">
import { useTextures } from './composables/useTextures'
import { ref, watch, computed } from 'vue'
import { Graphics, Rectangle, type TextStyle } from 'pixi.js'
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

const { availableAvatars, ensureAvatarTexture } = useTextures()

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
const isHovered = ref(false)

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
     const raceKey = String(props.avatar.race || 'human').toLowerCase()
     const library = availableAvatars.value[raceKey] || availableAvatars.value.human
     const list = Array.isArray(library) ? library : library?.[gender === 'female' ? 'female' : 'male']
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

  return ensureAvatarTexture(gender, pid, props.avatar.realm, props.avatar.race)
}

function getScale() {
  const tex = getTexture()
  if (!tex) return 1
  return (props.tileSize * 4.2) / Math.max(tex.width, tex.height)
}

function getAvatarSpriteScale() {
  return getScale() * (isHovered.value ? 1.05 : 1)
}

const drawFallback = (g: Graphics) => {
    g.clear()
    const radius = props.tileSize * (isHovered.value ? 0.56 : 0.5)
    g.circle(0, 0, radius)
    g.fill({ color: props.avatar.gender === 'female' ? 0xffaaaa : 0xaaaaff })
    g.stroke({ width: isHovered.value ? 4 : 2, color: isHovered.value ? 0xffe2a7 : 0x000000 })
}

const nameStyle = computed<TextStyle>(() => ({
    fontFamily: '"Microsoft YaHei", sans-serif',
    fontSize: 56,
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
}))

const hoverRingAlpha = computed(() => isHovered.value ? 0.72 : 0)
const hoverRingScale = computed(() => isHovered.value ? 1.04 : 0.92)
const interactionHitArea = computed(() =>
    new Rectangle(
        -props.tileSize * 1.35,
        -props.tileSize * 3.9,
        props.tileSize * 2.7,
        props.tileSize * 4.55,
    ),
)

const drawHoverRing = (g: Graphics) => {
    g.clear()
    if (!isHovered.value) return
    const radiusX = props.tileSize * 0.82
    const radiusY = props.tileSize * 0.34
    g.ellipse(0, 0, radiusX, radiusY)
    g.fill({ color: 0xf6d68a, alpha: 0.12 })
    g.stroke({ width: 3, color: 0xf6d68a, alpha: 0.76 })
}

function handlePointerTap() {
    useAudio().play('select')
    emit('select', {
        type: 'avatar',
        id: props.avatar.id,
        name: props.avatar.name
    })
}

const emojiStyle: TextStyle = {
    fontFamily: '"Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif',
    fontSize: 70,
    align: 'center',
}

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
    :alpha="isHovered ? 1 : 0.98"
    :hitArea="interactionHitArea"
    event-mode="static"
    cursor="pointer"
    @pointerenter="isHovered = true"
    @pointerover="isHovered = true"
    @pointermove="isHovered = true"
    @mouseenter="isHovered = true"
    @mouseover="isHovered = true"
    @pointerleave="isHovered = false"
    @pointerout="isHovered = false"
    @mouseleave="isHovered = false"
    @mouseout="isHovered = false"
    @pointertap="handlePointerTap"
  >
    <graphics
      v-if="isHovered"
      :key="`${avatar.id}-hover-ring`"
      :y="tileSize * 0.18"
      :alpha="hoverRingAlpha"
      :scale="hoverRingScale"
      event-mode="none"
      @effect="drawHoverRing"
    />

    <sprite
      v-if="getTexture()"
      :key="`${avatar.id}-${isHovered ? 'hover' : 'normal'}`"
      :texture="getTexture()"
      :anchor-x="0.5"
      :anchor-y="0.9" 
      :scale="getAvatarSpriteScale()"
      event-mode="none"
    />
    
    <graphics
      v-else
      :key="`${avatar.id}-${isHovered ? 'hover-fallback' : 'normal-fallback'}`"
      event-mode="none"
      @effect="drawFallback"
    />

    <!-- Emoji Bubble -->
    <container
      v-if="avatar.action_emoji"
      :x="tileSize * 0.6"
      :y="(getTexture() ? -tileSize * 3.5 : -tileSize * 1.2) + emojiBob"
      :z-index="100"
      event-mode="none"
    >
        <graphics event-mode="none" @effect="drawEmojiBg" />
        <text
            :text="avatar.action_emoji"
            :style="emojiStyle"
            :anchor="0.5"
            :scale="1.0"
            event-mode="none"
        />
    </container>

    <text
      :key="`${avatar.id}-name-${isHovered ? 'hover' : 'normal'}`"
      :text="avatar.name"
      :style="nameStyle"
      :anchor-x="0.5"
      :anchor-y="0"
      :y="isHovered ? 6 : 10"
      event-mode="none"
    />
  </container>
</template>
