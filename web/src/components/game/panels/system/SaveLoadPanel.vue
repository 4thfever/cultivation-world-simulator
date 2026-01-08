<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { gameApi, type SaveFileDTO } from '../../../../api/game'
import { useWorldStore } from '../../../../stores/world'
import { useUiStore } from '../../../../stores/ui'
import { useMessage } from 'naive-ui'

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
    const res = await gameApi.fetchSaves()
    saves.value = res.saves
  } catch (e) {
    message.error('获取存档列表失败')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  loading.value = true
  try {
    const res = await gameApi.saveGame()
    message.success(`存档成功: ${res.filename}`)
    await fetchSaves()
  } catch (e) {
    message.error('存档失败')
  } finally {
    loading.value = false
  }
}

async function handleLoad(filename: string) {
  if (!confirm(`确定要加载存档 ${filename} 吗？当前未保存的进度将丢失。`)) return

  loading.value = true
  try {
    // 调用后端加载存档，后端会设置 init_status = "in_progress"
    // App.vue 的轮询会检测到状态变化，显示加载界面，并在 ready 后重新初始化前端
    await gameApi.loadGame(filename)
    // 关闭菜单，让加载界面显示出来
    emit('close')
  } catch (e) {
    message.error('读档失败')
    loading.value = false
  }
  // 注意：不在这里设置 loading.value = false，因为菜单会关闭
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
    <div v-if="loading && saves.length === 0" class="loading">加载中...</div>
    
    <!-- Save Mode: New Save Button -->
    <template v-if="mode === 'save'">
      <div class="new-save-card" @click="handleSave">
        <div class="icon">+</div>
        <div>新建存档</div>
        <div class="sub">点击创建一个新的存档文件</div>
      </div>
    </template>

    <!-- Save List -->
    <div v-if="!loading && saves.length === 0" class="empty">暂无存档</div>
    <div 
      v-for="save in saves" 
      :key="save.filename"
      class="save-item"
      @click="mode === 'load' ? handleLoad(save.filename) : null"
    >
      <div class="save-info">
        <div class="save-time">{{ save.save_time }}</div>
        <div class="game-time">游戏时间: {{ save.game_time }}</div>
        <div class="filename">{{ save.filename }}</div>
      </div>
      <div v-if="mode === 'load'" class="load-btn">加载</div>
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
