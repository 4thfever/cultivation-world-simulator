import { onUnmounted, ref } from 'vue'

export function useDockResize(
  initialHeight: number,
  minHeight: number,
  maxHeight: number,
  isEnabled: () => boolean,
) {
  const dockHeight = ref(initialHeight)
  const isResizing = ref(false)

  let resizeStartY = 0
  let resizeStartHeight = 0

  function onResizeMouseMove(e: MouseEvent) {
    if (!isResizing.value) return
    const delta = resizeStartY - e.clientY
    dockHeight.value = Math.max(minHeight, Math.min(maxHeight, resizeStartHeight + delta))
  }

  function stopResize() {
    if (!isResizing.value) return
    isResizing.value = false
    document.removeEventListener('mousemove', onResizeMouseMove)
    document.removeEventListener('mouseup', stopResize)
  }

  function startResize(e: MouseEvent) {
    if (!isEnabled()) return
    e.preventDefault()
    resizeStartY = e.clientY
    resizeStartHeight = dockHeight.value
    isResizing.value = true
    document.addEventListener('mousemove', onResizeMouseMove)
    document.addEventListener('mouseup', stopResize)
  }

  onUnmounted(() => {
    stopResize()
  })

  return {
    dockHeight,
    isResizing,
    startResize,
    stopResize,
  }
}
