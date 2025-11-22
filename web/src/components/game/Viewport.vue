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

    // 1. 先计算新的缩放限制
    const fitScale = Math.min(props.screenWidth / worldWidth, props.screenHeight / worldHeight)
    
    // 2. 重要：在 fit() 之前先设置新的 clampZoom，或者先暂时移除旧的限制
    // 这里我们直接设置新的宽松限制
    viewport.clampZoom({ minScale: fitScale * 0.8, maxScale: 4.0 }) 

    // 3. 更新尺寸
    viewport.resize(props.screenWidth, props.screenHeight, worldWidth, worldHeight)
    
    // 4. 执行适配，并在中心位置
    viewport.fit(true, worldWidth, worldHeight)
    viewport.moveCenter(worldWidth / 2, worldHeight / 2)
    
    // 5. 如果当前缩放比预期的还要大（虽然 fit 应该已经处理了，但双保险），强制设置
    if (viewport.scaled > fitScale * 1.1) { // 允许一点误差
       viewport.setZoom(fitScale)
    }
}

watch(() => [props.screenWidth, props.screenHeight], ([w, h]) => {
  if (viewport) {
    // 1. Resize Viewport 视口尺寸更新
    viewport.resize(w, h, props.worldWidth, props.worldHeight)
    
    // 2. 重新计算适配比例
    const fitScale = Math.min(w / props.worldWidth, h / props.worldHeight)
    
    // 3. 设定缩放限制
    // 确保 maxScale 始终大于 minScale，防止地图极小时崩溃
    const minScale = fitScale * 0.8
    const maxScale = Math.max(4.0, minScale * 2.0)
    
    viewport.clampZoom({ minScale, maxScale }) 

    // 4. 自动修正缩放
    // 如果当前缩放过小（导致黑边），或者因为初始化时的尺寸问题导致缩放不正确，强制恢复到适配大小
    if (viewport.scaled < minScale * 0.95) {
       viewport.setZoom(fitScale)
       viewport.moveCenter(props.worldWidth / 2, props.worldHeight / 2)
    }
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
