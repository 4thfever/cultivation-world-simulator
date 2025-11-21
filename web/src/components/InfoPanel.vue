<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useGameStore } from '../stores/game'

const store = useGameStore()
const panelRef = ref<HTMLElement | null>(null)
let lastOpenAt = 0

const showObjectiveModal = ref(false)
const objectiveContent = ref('')

const title = computed(() => store.selectedTarget?.name ?? '')

watch(
  () => store.selectedTarget,
  (target) => {
    showObjectiveModal.value = false
    objectiveContent.value = ''
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

async function handleSetObjective() {
  if (!store.selectedTarget || !objectiveContent.value.trim()) return
  await store.setLongTermObjective(store.selectedTarget.id, objectiveContent.value)
  showObjectiveModal.value = false
  objectiveContent.value = ''
}

async function handleClearObjective() {
  if (!store.selectedTarget) return
  if (confirm('确定要清空该角色的长期目标吗？（系统将在之后自动重新生成）')) {
    await store.clearLongTermObjective(store.selectedTarget.id)
  }
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
    <div class="panel-actions" v-if="store.selectedTarget.type === 'avatar'">
      <button class="action-btn primary" @click="showObjectiveModal = true">设定长期目标</button>
      <button class="action-btn secondary" @click="handleClearObjective">清空长期目标</button>
    </div>

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

    <!-- 长期目标设定弹窗 -->
    <div v-if="showObjectiveModal" class="objective-modal">
      <div class="modal-title">设定长期目标</div>
      <textarea 
        v-model="objectiveContent" 
        placeholder="请输入该角色未来3-5年的长期目标..."
        class="objective-input"
      ></textarea>
      <div class="modal-actions">
        <button class="modal-btn confirm" @click="handleSetObjective" :disabled="!objectiveContent.trim()">确认</button>
        <button class="modal-btn cancel" @click="showObjectiveModal = false">取消</button>
      </div>
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
  overflow: visible; /* Allow modal to show outside */
}

.panel-actions {
  display: flex;
  flex-direction: column;
  padding: 12px 14px 4px;
  gap: 6px;
  background: rgba(38, 38, 38, 0.95);
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.action-btn {
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}

.action-btn.primary {
  background: #177ddc;
  color: white;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
}

.action-btn.primary:hover {
  background: #1890ff;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #aaa;
  padding: 5px 12px;
  font-size: 12px;
}

.action-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.25);
  color: #ccc;
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
  /* 确保body内容滚动时圆角 */
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
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

/* Modal Styles */
.objective-modal {
  position: absolute;
  top: 0;
  right: 100%; /* Position to the left of the panel */
  margin-right: 12px;
  width: 280px;
  background: rgba(32, 32, 32, 0.98);
  border: 1px solid #444;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 100;
}

.modal-title {
  font-size: 14px;
  font-weight: bold;
  color: #ddd;
}

.objective-input {
  width: 100%;
  height: 120px;
  background: #1f1f1f;
  border: 1px solid #444;
  border-radius: 4px;
  color: #eee;
  padding: 8px;
  resize: none;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.5;
  outline: none;
}

.objective-input:focus {
  border-color: #177ddc;
}

.modal-actions {
  display: flex;
  gap: 10px;
}

.modal-btn {
  flex: 1;
  padding: 6px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: opacity 0.2s;
}

.modal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-btn.confirm {
  background: #177ddc;
  color: white;
}

.modal-btn.confirm:hover:not(:disabled) {
  background: #1890ff;
}

.modal-btn.cancel {
  background: #444;
  color: #bbb;
}

.modal-btn.cancel:hover {
  background: #555;
  color: white;
}
</style>
