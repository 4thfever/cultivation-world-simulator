<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { gameApi } from '../api/game'
import { useWorldStore } from '../stores/world'
import { useUiStore } from '../stores/ui'
import { useMessage } from 'naive-ui'
import type { SaveFileDTO } from '../types/api'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const worldStore = useWorldStore()
const uiStore = useUiStore()
const message = useMessage()

const activeTab = ref<'save' | 'load'>('load')
const saves = ref<SaveFileDTO[]>([])
const loading = ref(false)

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
    await fetchSaves() // 刷新列表
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
    // 1. Call API
    await gameApi.loadGame(filename)
    
    // 2. Reset UI & World
    worldStore.reset()
    uiStore.clearSelection()
    uiStore.clearHoverCache()
    
    // 3. Re-initialize
    await worldStore.initialize()
    
    message.success('读档成功')
    emit('close')
  } catch (e) {
    message.error('读档失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (props.visible) {
    fetchSaves()
  }
})
</script>

<template>
  <div v-if="visible" class="system-menu-overlay" @click.self="emit('close')">
    <div class="system-menu">
      <div class="menu-header">
        <h2>系统菜单</h2>
        <button class="close-btn" @click="emit('close')">×</button>
      </div>
      
      <div class="menu-tabs">
        <button 
          :class="{ active: activeTab === 'save' }"
          @click="activeTab = 'save'; fetchSaves()"
        >
          保存游戏
        </button>
        <button 
          :class="{ active: activeTab === 'load' }"
          @click="activeTab = 'load'; fetchSaves()"
        >
          加载游戏
        </button>
      </div>

      <div class="menu-content">
        <div v-if="loading" class="loading">处理中...</div>
        
        <div v-else-if="activeTab === 'save'" class="save-panel">
          <div class="new-save-card" @click="handleSave">
            <div class="icon">+</div>
            <div>新建存档</div>
            <div class="sub">点击创建一个新的存档文件</div>
          </div>
        </div>

        <div v-else class="load-panel">
          <div v-if="saves.length === 0" class="empty">暂无存档</div>
          <div 
            v-for="save in saves" 
            :key="save.filename"
            class="save-item"
            @click="handleLoad(save.filename)"
          >
            <div class="save-info">
              <div class="save-time">{{ save.save_time }}</div>
              <div class="game-time">游戏时间: {{ save.game_time }}</div>
              <div class="filename">{{ save.filename }}</div>
            </div>
            <div class="load-btn">加载</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.system-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.system-menu {
  background: #1a1a1a;
  width: 600px;
  height: 500px;
  border: 1px solid #333;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}

.menu-header {
  padding: 16px;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.menu-header h2 {
  margin: 0;
  font-size: 18px;
  color: #ddd;
}

.close-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 24px;
  cursor: pointer;
}

.menu-tabs {
  display: flex;
  border-bottom: 1px solid #333;
}

.menu-tabs button {
  flex: 1;
  padding: 12px;
  background: #222;
  border: none;
  color: #888;
  cursor: pointer;
  transition: all 0.2s;
}

.menu-tabs button:hover {
  background: #2a2a2a;
}

.menu-tabs button.active {
  background: #1a1a1a;
  color: #fff;
  border-bottom: 2px solid #4a9eff;
}

.menu-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.save-panel {
  display: flex;
  justify-content: center;
  padding-top: 40px;
}

.new-save-card {
  width: 200px;
  height: 150px;
  border: 2px dashed #444;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #888;
}

.new-save-card:hover {
  border-color: #666;
  background: #222;
  color: #fff;
}

.new-save-card .icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.new-save-card .sub {
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.save-item {
  background: #222;
  border: 1px solid #333;
  padding: 12px;
  margin-bottom: 10px;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background 0.2s;
}

.save-item:hover {
  background: #2a2a2a;
  border-color: #444;
}

.save-info .save-time {
  color: #fff;
  font-weight: bold;
  font-size: 14px;
}

.save-info .game-time {
  color: #4a9eff;
  font-size: 13px;
  margin: 4px 0;
}

.save-info .filename {
  color: #666;
  font-size: 12px;
  font-family: monospace;
}

.load-btn {
  background: #333;
  color: #ddd;
  border: 1px solid #444;
  padding: 6px 16px;
  border-radius: 4px;
}

.loading {
  text-align: center;
  color: #888;
  padding: 40px;
}

.empty {
  text-align: center;
  color: #666;
  padding: 40px;
}
</style>
