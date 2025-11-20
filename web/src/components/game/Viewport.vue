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
    const { worldWidth, worldHeight } = props
    // Don't fit if world is default small
    if (worldWidth < 100) return 

    viewport.resize(props.screenWidth, props.screenHeight, worldWidth, worldHeight)
    viewport.fit(true, worldWidth, worldHeight)
    
    const fitScale = Math.min(props.screenWidth / worldWidth, props.screenHeight / worldHeight)
    // Allow zooming out a bit more than fit
    viewport.clampZoom({ minScale: fitScale * 0.8, maxScale: 4.0 }) 
    
    // If current zoom is weird, reset
    if (viewport.scaled < fitScale) viewport.setZoom(fitScale)
}

watch(() => [props.screenWidth, props.screenHeight], ([w, h]) => {
  if (viewport) {
    viewport.resize(w, h, props.worldWidth, props.worldHeight)
    // Optional: Refit on significant resize or just clamp?
    // clampZoom updates automatically if minScale is not dynamic? 
    // No, we set minScale manually. We should re-clamp.
    const fitScale = Math.min(w / props.worldWidth, h / props.worldHeight)
    viewport.clampZoom({ minScale: fitScale * 0.8, maxScale: 4.0 }) 
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
