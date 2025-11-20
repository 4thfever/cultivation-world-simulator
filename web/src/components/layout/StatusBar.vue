<script setup lang="ts">
import { useGameStore } from '../../stores/game'

const store = useGameStore()
</script>

<template>
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
</template>

<style scoped>
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

</style>

