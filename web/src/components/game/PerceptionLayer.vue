<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { Container, Graphics } from 'pixi.js'
import { useUiStore } from '../../stores/ui'
import { useAvatarStore } from '../../stores/avatar'
import type { AvatarDetail } from '../../types/core'

const props = defineProps<{
  width: number
  height: number
}>()

const TILE_SIZE = 64
const container = ref<Container>()
const uiStore = useUiStore()
const avatarStore = useAvatarStore()

let maskGraphics: Graphics | null = null

function updateMask() {
  if (!maskGraphics) return
  
  const g = maskGraphics
  g.clear()
  
  const target = uiStore.selectedTarget
  const detail = uiStore.detailData as AvatarDetail | null
  
  if (!target || target.type !== 'avatar' || !detail || detail.observation_radius === undefined) {
    return
  }

  const avatarId = target.id
  const avatar = avatarStore.avatars.get(avatarId)
  
  if (!avatar) return
  
  // 1. 绘制外层大矩形并填充
  g.rect(0, 0, props.width, props.height)
  g.fill({ color: 0x000000, alpha: 0.6 })
  
  const radius = detail.observation_radius
  const centerX = avatar.x
  const centerY = avatar.y
  
  // 2. 绘制想要挖空的形状并调用 cut()
  for (let dx = -radius; dx <= radius; dx++) {
    for (let dy = -radius; dy <= radius; dy++) {
      if (Math.abs(dx) + Math.abs(dy) <= radius) {
        const tileX = centerX + dx
        const tileY = centerY + dy
        
        // 如果格子在地图范围内，可以优化一下，不过直接画在外面 cut 也没影响
        g.rect(tileX * TILE_SIZE, tileY * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        g.cut()
      }
    }
  }
}

onMounted(() => {
  if (container.value) {
    maskGraphics = new Graphics()
    maskGraphics.eventMode = 'none'
    container.value.addChild(maskGraphics)
    updateMask()
  }
})

onUnmounted(() => {
  if (maskGraphics) {
    maskGraphics.destroy()
    maskGraphics = null
  }
})

watch(
  () => [
    uiStore.selectedTarget, 
    uiStore.detailData, 
    // 监听角色坐标变化
    uiStore.selectedTarget?.type === 'avatar' ? avatarStore.avatars.get(uiStore.selectedTarget.id)?.x : null,
    uiStore.selectedTarget?.type === 'avatar' ? avatarStore.avatars.get(uiStore.selectedTarget.id)?.y : null
  ],
  () => {
    updateMask()
  },
  { deep: true }
)
</script>

<template>
  <container ref="container" :z-index="250" event-mode="none" />
</template>
