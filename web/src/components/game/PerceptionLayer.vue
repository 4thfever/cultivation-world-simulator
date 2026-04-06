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

function getSelectedAvatarDetail(): AvatarDetail | null {
  return uiStore.selectedTarget?.type === 'avatar' ? uiStore.detailData as AvatarDetail | null : null
}

function updateMask() {
  if (!maskGraphics) return
  
  const g = maskGraphics
  g.clear()
  
  const target = uiStore.selectedTarget
  const detail = getSelectedAvatarDetail()
  
  if (!target || target.type !== 'avatar' || !detail || detail.observation_radius === undefined) {
    return
  }

  const avatarId = target.id
  const avatar = avatarStore.avatars.get(avatarId)
  
  if (!avatar) return
  
  const radius = detail.observation_radius
  const centerX = avatar.x
  const centerY = avatar.y
  const rows = Math.ceil(props.height / TILE_SIZE)
  const cols = Math.ceil(props.width / TILE_SIZE)
  
  // 逐格正向绘制视野外黑幕，保持原先单层遮罩的不透明度。
  for (let tileY = 0; tileY < rows; tileY++) {
    for (let tileX = 0; tileX < cols; tileX++) {
      const distance = Math.abs(tileX - centerX) + Math.abs(tileY - centerY)

      if (distance <= radius) {
        continue
      }

      g.rect(tileX * TILE_SIZE, tileY * TILE_SIZE, TILE_SIZE, TILE_SIZE)
      g.fill({ color: 0x000000, alpha: 0.6 })
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
