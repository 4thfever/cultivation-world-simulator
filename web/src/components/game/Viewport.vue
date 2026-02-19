<script setup lang="ts">
import { Viewport as PixiViewport } from 'pixi-viewport'
import { useApplication } from 'vue3-pixi'
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Container } from 'pixi.js'

const props = defineProps<{
  screenWidth: number
  screenHeight: number
  worldWidth: number
  worldHeight: number
}>()

const app = useApplication()
const containerRef = ref<Container>()
let viewport: PixiViewport | null = null

onMounted(async () => {
  await nextTick()
  if (!containerRef.value || !app.value) return

  viewport = new PixiViewport({
    screenWidth: props.screenWidth,
    screenHeight: props.screenHeight,
    worldWidth: props.worldWidth,
    worldHeight: props.worldHeight,
    events: app.value.renderer.events
  })

  viewport
    .drag()
    .pinch()
    .wheel()
    .decelerate({ friction: 0.9 })

  // Initial Fit
  fitMap()

  const container = containerRef.value
  if (container.parent) container.parent.removeChild(container)
  app.value.stage.addChild(viewport)
  viewport.addChild(container)
  
  ;(window as any).__viewport = viewport
})

function fitMap() {
    if (!viewport) return
    const { worldWidth, worldHeight, screenWidth, screenHeight } = props
    if (worldWidth < 100) return

    const fitScale = Math.min(screenWidth / worldWidth, screenHeight / worldHeight)
    viewport.clampZoom({ minScale: fitScale * 0.8, maxScale: 4.0 })
    viewport.resize(screenWidth, screenHeight, worldWidth, worldHeight)
    viewport.fit(true, worldWidth, worldHeight)
    viewport.moveCenter(worldWidth / 2, worldHeight / 2)

    if (viewport.scaled > fitScale * 1.1) {
        viewport.setZoom(fitScale)
    }
}

watch(() => [props.screenWidth, props.screenHeight], () => {
  if (viewport) {
    // 窗口尺寸变化时，重新适配地图。
    fitMap()
  }
})

watch(() => [props.worldWidth, props.worldHeight], () => {
    fitMap()
})

onUnmounted(() => {
  if (viewport) {
    viewport.destroy({ children: false })
  }
})
</script>

<template>
  <container ref="containerRef">
    <slot />
  </container>
</template>
