import { ref, onMounted, onUnmounted } from 'vue'

const MIN_SIDEBAR_WIDTH = 300

export function useSidebarResize(initialWidth = 400) {
  const sidebarWidth = ref(initialWidth)
  const isResizing = ref(false)

  function getMaxSidebarWidth() {
    return Math.floor(window.innerWidth * 0.5)
  }

  function onResizerMouseDown(e: MouseEvent) {
    e.preventDefault()
    isResizing.value = true
    document.addEventListener('mousemove', onResizerMouseMove)
    document.addEventListener('mouseup', onResizerMouseUp)
  }

  function onResizerMouseMove(e: MouseEvent) {
    if (!isResizing.value) return
    const newWidth = window.innerWidth - e.clientX
    const maxWidth = getMaxSidebarWidth()
    sidebarWidth.value = Math.max(MIN_SIDEBAR_WIDTH, Math.min(newWidth, maxWidth))
  }

  function onResizerMouseUp() {
    isResizing.value = false
    document.removeEventListener('mousemove', onResizerMouseMove)
    document.removeEventListener('mouseup', onResizerMouseUp)
  }

  function onWindowResize() {
    const maxWidth = getMaxSidebarWidth()
    if (sidebarWidth.value > maxWidth) {
      sidebarWidth.value = maxWidth
    }
  }

  onMounted(() => {
    window.addEventListener('resize', onWindowResize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', onWindowResize)
    document.removeEventListener('mousemove', onResizerMouseMove)
    document.removeEventListener('mouseup', onResizerMouseUp)
  })

  return {
    sidebarWidth,
    isResizing,
    onResizerMouseDown
  }
}
