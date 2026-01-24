<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
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

async function handleSave() {
  loading.value = true
  try {
    const res = await systemApi.saveGame()
    message.success(t('save_load.save_success', { filename: res.filename }))
    await fetchSaves()
  } catch (e) {
    message.error(t('save_load.save_failed'))
  } finally {
    loading.value = false
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

watch(() => props.mode, () => {
  fetchSaves()
})

onMounted(() => {
  fetchSaves()
})
</script>

<template>
  <div :class="mode === 'save' ? 'save-panel' : 'load-panel'">
    <div v-if="loading && saves.length === 0" class="loading">{{ t('save_load.loading') }}</div>
    
    <!-- Save Mode: New Save Button -->
    <template v-if="mode === 'save'">
      <div class="new-save-card" @click="handleSave">
        <div class="icon">+</div>
        <div>{{ t('save_load.new_save') }}</div>
        <div class="sub">{{ t('save_load.new_save_desc') }}</div>
      </div>
    </template>

    <!-- Save List -->
    <div v-if="!loading && saves.length === 0" class="empty">{{ t('save_load.empty') }}</div>
    <div 
      v-for="save in saves" 
      :key="save.filename"
      class="save-item"
      @click="mode === 'load' ? handleLoad(save.filename) : null"
    >
      <div class="save-info">
        <div class="save-time">{{ save.save_time }}</div>
        <div class="game-time">{{ t('save_load.game_time', { time: save.game_time }) }}</div>
        <div class="filename">{{ save.filename }}</div>
      </div>
      <div v-if="mode === 'load'" class="load-btn">{{ t('save_load.load') }}</div>
    </div>
  </div>
</template>

<style scoped>
.save-panel, .load-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.save-panel {
  align-items: center;
  padding-top: 3em;
}

.new-save-card {
  width: 15em;
  height: 11em;
  border: 2px dashed #444;
  border-radius: 0.5em;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #888;
  margin-bottom: 3em;
}

.new-save-card:hover {
  border-color: #666;
  background: #222;
  color: #fff;
}

.new-save-card .icon {
  font-size: 3em;
  margin-bottom: 0.2em;
}

.new-save-card .sub {
  font-size: 0.85em;
  color: #666;
  margin-top: 0.4em;
}

.save-item {
  background: #222;
  border: 1px solid #333;
  padding: 0.8em;
  margin-bottom: 0.8em;
  border-radius: 0.3em;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background 0.2s;
  width: 100%;
}

.save-panel .save-item {
    cursor: default; 
    width: 100%;
    max-width: 45em;
}

.save-item:hover {
  background: #2a2a2a;
  border-color: #444;
}

.save-info .save-time {
  color: #fff;
  font-weight: bold;
  font-size: 1em;
}

.save-info .game-time {
  color: #4a9eff;
  font-size: 0.9em;
  margin: 0.3em 0;
}

.save-info .filename {
  color: #666;
  font-size: 0.85em;
  font-family: monospace;
}

.load-btn {
  background: #333;
  color: #ddd;
  border: 1px solid #444;
  padding: 0.4em 1em;
  border-radius: 0.3em;
  font-size: 0.9em;
}

.loading, .empty {
  text-align: center;
  color: #888;
  padding: 3em;
  width: 100%;
}
</style>
