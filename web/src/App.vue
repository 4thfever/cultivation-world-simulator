<script setup lang="ts">
import { onMounted } from 'vue'
import { useGameStore } from './stores/game'
import { NCard, NStatistic, NGrid, NGridItem } from 'naive-ui'

const store = useGameStore()

onMounted(async () => {
  await store.fetchInitialState()
  store.connect()
})
</script>

<template>
  <div class="container">
    <header>
      <h1>修仙世界模拟器 (Web版)</h1>
      <div class="status">
        <span :class="{ connected: store.isConnected }">
          {{ store.isConnected ? '已连接' : '断开连接' }}
        </span>
      </div>
    </header>

    <main>
      <n-grid :cols="4" :x-gap="12">
        <n-grid-item>
          <n-card>
            <n-statistic label="年份" :value="store.year" />
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card>
            <n-statistic label="月份" :value="store.month" />
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card>
            <n-statistic label="当前活跃角色" :value="store.avatarList.length" />
          </n-card>
        </n-grid-item>
      </n-grid>

      <div class="debug-avatars">
        <h3>角色列表 (Debug)</h3>
        <ul>
          <li v-for="av in store.avatarList.slice(0, 10)" :key="av.id">
            {{ av.name || 'Unknown' }} [{{ av.x }}, {{ av.y }}] - {{ av.action }}
          </li>
        </ul>
      </div>
    </main>
  </div>
</template>

<style scoped>
.container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.status span {
  padding: 4px 8px;
  background: #ff4d4f;
  color: white;
  border-radius: 4px;
}

.status span.connected {
  background: #52c41a;
}

.debug-avatars {
  margin-top: 20px;
  background: #f5f5f5;
  padding: 10px;
  border-radius: 8px;
}
</style>

