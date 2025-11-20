<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useGameStore } from '../stores/game'

const store = useGameStore()
const panelRef = ref<HTMLElement | null>(null)
let lastOpenAt = 0

const title = computed(() => store.selectedTarget?.name ?? '')

watch(
  () => store.selectedTarget,
  (target) => {
    if (target) {
      lastOpenAt = performance.now()
    }
  }
)

function handleDocumentPointerDown(event: PointerEvent) {
  if (!store.selectedTarget || !panelRef.value) return
  const target = event.target as Node | null
  if (target && panelRef.value.contains(target)) return

  const now = performance.now()
  if (now - lastOpenAt < 50) {
    return
  }
  store.closeInfoPanel()
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
})

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
})
</script>

<template>
  <div
    v-if="store.selectedTarget"
    class="info-panel"
    ref="panelRef"
  >
    <div class="info-header">
      <div class="info-title">{{ title || '详情' }}</div>
      <button class="close-btn" type="button" @click="store.closeInfoPanel()">×</button>
    </div>
    <div class="info-body">
      <div v-if="store.infoLoading" class="placeholder">加载中...</div>
      <div v-else-if="store.infoError" class="placeholder error">
        {{ store.infoError }}
      </div>
      <ul v-else-if="store.hoverInfo.length" class="info-list">
        <li v-for="(line, index) in store.hoverInfo" :key="index">
          <template v-if="line.length">
            <span
              v-for="(segment, segIndex) in line"
              :key="segIndex"
              class="info-segment"
              :style="segment.color ? { color: segment.color } : undefined"
            >
              {{ segment.text || ' ' }}
            </span>
          </template>
          <span v-else class="info-segment">&nbsp;</span>
        </li>
      </ul>
      <div v-else class="placeholder">暂无信息</div>
    </div>
  </div>
</template>

<style scoped>
.info-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 320px;
  max-height: calc(100vh - 40px);
  background: rgba(24, 24, 24, 0.96);
  border: 1px solid #333;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45);
  color: #eee;
  pointer-events: auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.info-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(38, 38, 38, 0.95);
  border-bottom: 1px solid #333;
}

.info-title {
  font-size: 16px;
  font-weight: bold;
}

.close-btn {
  background: transparent;
  border: none;
  color: #999;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 2px 4px;
}

.close-btn:hover {
  color: #fff;
}

.info-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
}

.info-list li + li {
  margin-top: 6px;
}

.info-segment {
  white-space: pre-wrap;
}

.placeholder {
  font-size: 13px;
  color: #888;
}

.placeholder.error {
  color: #ff7875;
}
</style>

