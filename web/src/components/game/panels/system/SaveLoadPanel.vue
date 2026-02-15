<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { NModal, NInput, NButton, NSpin, NTooltip } from 'naive-ui'
import { systemApi } from '../../../../api'
import type { SaveFileDTO } from '../../../../types/api'
import { useWorldStore } from '../../../../stores/world'
import { useUiStore } from '../../../../stores/ui'
import { useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  mode: 'save' | 'load'
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const worldStore = useWorldStore()
const uiStore = useUiStore()
const message = useMessage()
const loading = ref(false)
const saves = ref<SaveFileDTO[]>([])

// 保存对话框状态
const showSaveModal = ref(false)
const saveName = ref('')
const saving = ref(false)

// 名称验证
const nameError = computed(() => {
  if (!saveName.value) return ''
  if (saveName.value.length > 50) {
    return t('save_load.name_too_long')
  }
  // 只允许中文、字母、数字和下划线
  const pattern = /^[\w\u4e00-\u9fff]+$/
  if (!pattern.test(saveName.value)) {
    return t('save_load.name_invalid_chars')
  }
  return ''
})

async function fetchSaves() {
  loading.value = true
  try {
    const res = await systemApi.fetchSaves()
    saves.value = res.saves
  } catch (e) {
    message.error(t('save_load.fetch_failed'))
  } finally {
    loading.value = false
  }
}

// 打开保存对话框
function openSaveModal() {
  saveName.value = ''
  showSaveModal.value = true
}

// 快速保存（不输入名称）
async function handleQuickSave() {
  saving.value = true
  try {
    const res = await systemApi.saveGame()
    message.success(t('save_load.save_success', { filename: res.filename }))
    await fetchSaves()
  } catch (e) {
    message.error(t('save_load.save_failed'))
  } finally {
    saving.value = false
  }
}

// 带名称保存
async function handleSaveWithName() {
  if (nameError.value) return

  saving.value = true
  try {
    const customName = saveName.value.trim() || undefined
    const res = await systemApi.saveGame(customName)
    message.success(t('save_load.save_success', { filename: res.filename }))
    showSaveModal.value = false
    saveName.value = ''
    await fetchSaves()
  } catch (e) {
    message.error(t('save_load.save_failed'))
  } finally {
    saving.value = false
  }
}

async function handleLoad(filename: string) {
  if (!confirm(t('save_load.load_confirm', { filename }))) return

  loading.value = true
  try {
    await systemApi.loadGame(filename)
    worldStore.reset()
    uiStore.clearSelection()
    await worldStore.initialize()
    message.success(t('save_load.load_success'))
    emit('close')
  } catch (e) {
    message.error(t('save_load.load_failed'))
  } finally {
    loading.value = false
  }
}

async function handleDelete(filename: string) {
  if (!confirm(t('save_load.delete_confirm', { filename }))) return

  loading.value = true
  try {
    await systemApi.deleteSave(filename)
    message.success(t('save_load.delete_success'))
    await fetchSaves()
  } catch (e) {
    message.error(t('save_load.delete_failed'))
  } finally {
    loading.value = false
  }
}

// 格式化保存时间
function formatSaveTime(isoTime: string): string {
  if (!isoTime) return ''
  try {
    const date = new Date(isoTime)
    return date.toLocaleString()
  } catch {
    return isoTime
  }
}

// 获取存档显示名称
function getSaveDisplayName(save: SaveFileDTO): string {
  if (save.custom_name) {
    return save.custom_name
  }
  // 从文件名提取时间部分
  return save.filename.replace('.json', '')
}

watch(() => props.mode, () => {
  fetchSaves()
})

onMounted(() => {
  fetchSaves()
})
</script>

<template>
  <div :class="mode === 'save' ? 'save-panel' : 'load-panel'">
    <div v-if="loading && saves.length === 0" class="loading">
      <NSpin size="medium" />
      <span>{{ t('save_load.loading') }}</span>
    </div>

    <!-- Save Mode: Action Buttons -->
    <template v-if="mode === 'save'">
      <div class="save-actions">
        <div class="new-save-card" @click="openSaveModal">
          <div class="icon">+</div>
          <div>{{ t('save_load.new_save') }}</div>
          <div class="sub">{{ t('save_load.new_save_desc') }}</div>
        </div>
        <div class="quick-save-card" @click="handleQuickSave">
          <div class="icon">
            <NSpin v-if="saving" size="small" />
            <span v-else>&#9889;</span>
          </div>
          <div>{{ t('save_load.quick_save') }}</div>
          <div class="sub">{{ t('save_load.quick_save_desc') }}</div>
        </div>
      </div>
    </template>

    <!-- Save List -->
    <div v-if="!loading && saves.length === 0" class="empty">{{ t('save_load.empty') }}</div>

    <div class="saves-list">
      <div
        v-for="save in saves"
        :key="save.filename"
        class="save-item"
        @click="mode === 'load' ? handleLoad(save.filename) : null"
      >
        <div class="save-info">
          <div class="save-header">
            <span class="save-name">{{ getSaveDisplayName(save) }}</span>
          </div>
          <div class="save-meta">
            <span class="game-time">{{ t('save_load.game_time', { time: save.game_time }) }}</span>
            <span class="divider">|</span>
            <span class="avatar-count">{{ t('save_load.avatar_count', { alive: save.alive_count, total: save.avatar_count }) }}</span>
            <span class="divider">|</span>
            <span class="event-count">{{ t('save_load.event_count', { count: save.event_count }) }}</span>
          </div>
          <div class="save-footer">
            <span class="save-time">{{ formatSaveTime(save.save_time) }}</span>
            <span class="version">v{{ save.version }}</span>
          </div>
        </div>
        <div v-if="mode === 'load'" class="load-actions">
           <NButton 
             type="error" 
             size="small" 
             secondary 
             @click.stop="handleDelete(save.filename)"
           >
             {{ t('save_load.delete') }}
           </NButton>
           <NButton
             size="small"
             @click.stop="handleLoad(save.filename)"
           >
             {{ t('save_load.load') }}
           </NButton>
        </div>
      </div>
    </div>

    <!-- Save Modal -->
    <NModal
      v-model:show="showSaveModal"
      preset="card"
      :title="t('save_load.save_modal_title')"
      style="width: 400px;"
      :mask-closable="!saving"
      :closable="!saving"
    >
      <div class="save-modal-content">
        <p class="hint">{{ t('save_load.name_hint') }}</p>
        <NInput
          v-model:value="saveName"
          :placeholder="t('save_load.name_placeholder')"
          :status="nameError ? 'error' : undefined"
          :disabled="saving"
          @keyup.enter="handleSaveWithName"
        />
        <p v-if="nameError" class="error-text">{{ nameError }}</p>
        <p v-else class="tip-text">{{ t('save_load.name_tip') }}</p>
      </div>
      <template #footer>
        <div class="modal-footer">
          <NButton :disabled="saving" @click="showSaveModal = false">
            {{ t('common.cancel') }}
          </NButton>
          <NButton
            type="primary"
            :loading="saving"
            :disabled="!!nameError"
            @click="handleSaveWithName"
          >
            {{ t('save_load.save_confirm') }}
          </NButton>
        </div>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.save-panel, .load-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.save-panel, .load-panel {
  align-items: center;
  padding-top: 2em;
}

.save-actions {
  display: flex;
  gap: 1.5em;
  margin-bottom: 2em;
}

.new-save-card, .quick-save-card {
  width: 12em;
  height: 9em;
  border: 2px dashed #444;
  border-radius: 0.5em;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #888;
}

.new-save-card:hover, .quick-save-card:hover {
  border-color: #666;
  background: #222;
  color: #fff;
}

.quick-save-card {
  border-color: #3a5a3a;
}

.quick-save-card:hover {
  border-color: #4a7a4a;
  background: #1a2a1a;
}

.new-save-card .icon, .quick-save-card .icon {
  font-size: 2.5em;
  margin-bottom: 0.2em;
}

.new-save-card .sub, .quick-save-card .sub {
  font-size: 0.75em;
  color: #666;
  margin-top: 0.3em;
}

.saves-list {
  width: 100%;
  max-width: 50em;
  overflow-y: auto;
  flex: 1;
}

.save-item {
  background: #222;
  border: 1px solid #333;
  padding: 0.8em 1em;
  margin-bottom: 0.6em;
  border-radius: 0.4em;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s;
}

.save-panel .save-item {
  cursor: default;
}

.save-item:hover {
  background: #2a2a2a;
  border-color: #444;
}

.save-info {
  flex: 1;
}

.save-header {
  display: flex;
  align-items: center;
  gap: 0.6em;
  margin-bottom: 0.4em;
}

.save-name {
  color: #fff;
  font-weight: bold;
  font-size: 1.05em;
}

.save-meta {
  display: flex;
  align-items: center;
  gap: 0.5em;
  margin-bottom: 0.3em;
  font-size: 0.85em;
}

.game-time {
  color: #4a9eff;
}

.avatar-count {
  color: #7acc7a;
}

.event-count {
  color: #cc9a7a;
}

.divider {
  color: #444;
}

.save-footer {
  display: flex;
  align-items: center;
  gap: 1em;
  font-size: 0.8em;
  color: #666;
}

.version {
  font-family: monospace;
}

.load-actions {
  display: flex;
  gap: 1em;
  align-items: center;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.8em;
  color: #888;
  padding: 3em;
  width: 100%;
}

.empty {
  text-align: center;
  color: #888;
  padding: 3em;
  width: 100%;
}

/* Save Modal */
.save-modal-content {
  display: flex;
  flex-direction: column;
  gap: 0.8em;
}

.hint {
  color: #aaa;
  margin: 0;
  font-size: 0.9em;
}

.error-text {
  color: #e55;
  margin: 0;
  font-size: 0.85em;
}

.tip-text {
  color: #888;
  margin: 0;
  font-size: 0.85em;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.8em;
}
</style>
