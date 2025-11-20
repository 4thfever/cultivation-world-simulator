<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useGameStore } from './stores/game'
import { NConfigProvider, darkTheme, NSelect } from 'naive-ui'
import GameCanvas from './components/game/GameCanvas.vue'

const store = useGameStore()
const filterValue = ref('all')

const filterOptions = computed(() => [
  { label: '所有人', value: 'all' },
  ...store.avatarList.map(a => ({ label: a.name, value: a.id }))
])

onMounted(async () => {
  await store.fetchInitialState()
  store.connect()
})
</script>

<template>
  <n-config-provider :theme="darkTheme">
    <div class="app-layout">
      <!-- 顶部状态栏 -->
      <header class="top-bar">
        <div class="left">
          <span class="title">修仙模拟器</span>
          <span class="status-dot" :class="{ connected: store.isConnected }"></span>
        </div>
        <div class="center">
          <span class="time">{{ store.year }}年 {{ store.month }}月</span>
        </div>
        <div class="right">
          <span>修士: {{ store.avatarList.length }}</span>
        </div>
      </header>

      <div class="main-content">
        <!-- 地图区域 (占据主要空间) -->
        <div class="map-container">
          <GameCanvas />
        </div>

        <!-- 右侧侧边栏 (固定宽度) -->
        <aside class="sidebar">
          <div class="sidebar-section">
            <div class="sidebar-header">
                <h3>事件记录</h3>
                <n-select 
                    v-model:value="filterValue" 
                    :options="filterOptions" 
                    size="tiny" 
                    class="event-filter"
                />
            </div>
            <div v-if="store.events.length === 0" class="empty">暂无事件</div>
            <div v-else class="event-list">
                <div v-for="(event, index) in store.events" :key="index" class="event-item">
                    {{ event }}
                </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </n-config-provider>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  background: #000;
  color: #eee;
  overflow: hidden;
}

.top-bar {
  height: 36px;
  background: #1f1f1f;
  border-bottom: 1px solid #333;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  font-size: 14px;
  z-index: 10;
}

.top-bar .title {
  font-weight: bold;
  margin-right: 8px;
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ff4d4f;
}
.status-dot.connected {
  background: #52c41a;
}

.main-content {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.map-container {
  flex: 1;
  position: relative;
  background: #111;
  overflow: hidden;
}

.sidebar {
  width: 400px; /* Increased width */
  background: #181818;
  border-left: 1px solid #333;
  display: flex;
  flex-direction: column;
  z-index: 20;
}

.sidebar-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: #222;
    border-bottom: 1px solid #333;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 13px;
  white-space: nowrap;
}

.event-filter {
    width: 200px;
}

.event-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 12px;
}

.event-item {
    font-size: 12px;
    color: #ccc;
    padding: 4px 0;
    border-bottom: 1px solid #333;
}

.event-item:last-child {
    border-bottom: none;
}

.empty {
  padding: 20px;
  text-align: center;
  color: #666;
  font-size: 12px;
}
</style>
