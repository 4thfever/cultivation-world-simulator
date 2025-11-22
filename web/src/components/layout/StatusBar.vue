<script setup lang="ts">
import { useWorldStore } from '../../stores/world'
import { gameSocket } from '../../api/socket'
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { NPopover } from 'naive-ui'

const store = useWorldStore()
const isConnected = ref(false)

// Update status locally since socket store is bare-bones
let cleanup: (() => void) | undefined;

onMounted(() => {
  cleanup = gameSocket.onStatusChange((status) => {
    isConnected.value = status
  })
})

onUnmounted(() => {
  if (cleanup) cleanup()
})

const phenomenonColor = computed(() => {
  const p = store.currentPhenomenon;
  if (!p) return '#ccc';
  switch (p.rarity) {
    case 'N': return '#ccc';
    case 'R': return '#4dabf7'; // Blue
    case 'SR': return '#a0d911'; // Lime
    case 'SSR': return '#fa8c16'; // Orange/Gold
    default: return '#ccc';
  }
})
</script>

<template>
  <header class="top-bar">
    <div class="left">
      <span class="title">AI修仙世界模拟器</span>
      <span class="status-dot" :class="{ connected: isConnected }"></span>
    </div>
    <div class="center">
      <span class="time">{{ store.year }}年 {{ store.month }}月</span>
      
      <!-- 天地灵机 -->
      <div class="phenomenon" v-if="store.currentPhenomenon">
        <span class="divider">|</span>
        <n-popover trigger="hover" placement="bottom" style="max-width: 300px;">
          <template #trigger>
            <span class="phenomenon-name" :style="{ color: phenomenonColor }">
              [{{ store.currentPhenomenon.name }}]
            </span>
          </template>
          <div class="phenomenon-card">
             <div class="p-header" :style="{ color: phenomenonColor }">
               <span class="p-title">{{ store.currentPhenomenon.name }}</span>
               <span class="p-rarity">{{ store.currentPhenomenon.rarity }}</span>
             </div>
             <div class="p-desc">{{ store.currentPhenomenon.desc }}</div>
             
             <!-- 效果描述 -->
             <div class="effect-block" v-if="store.currentPhenomenon.effect_desc">
               <div class="effect-label">效果：</div>
               <div class="effect-content">{{ store.currentPhenomenon.effect_desc }}</div>
             </div>

             <div class="p-duration" v-if="store.currentPhenomenon.duration_years">
                持续 {{ store.currentPhenomenon.duration_years }} 年
             </div>
          </div>
        </n-popover>
      </div>
    </div>
    <div class="author">
      肥桥今天吃什么的<a
        class="author-link"
        href="https://space.bilibili.com/527346837"
        target="_blank"
        rel="noopener"
      >B站空间</a>
      <a
        class="author-link"
        href="https://github.com/4thfever/cultivation-world-simulator"
        target="_blank"
        rel="noopener"
      >
        Github仓库
      </a>
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
  gap: 16px;
}

.top-bar .title {
  font-weight: bold;
  margin-right: 8px;
}

.center {
  display: flex;
  align-items: center;
  gap: 10px;
}

.phenomenon {
  display: flex;
  align-items: center;
  gap: 10px;
}

.divider {
  color: #444;
}

.phenomenon-name {
  cursor: help;
  font-weight: bold;
}

.phenomenon-card {
  padding: 4px 0;
}

.p-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: bold;
  font-size: 15px;
  border-bottom: 1px solid #333;
  padding-bottom: 4px;
}

.p-rarity {
  font-size: 12px;
  opacity: 0.8;
  border: 1px solid currentColor;
  padding: 0 4px;
  border-radius: 2px;
}

.p-desc {
  font-size: 13px;
  color: #ddd;
  line-height: 1.5;
  margin-bottom: 8px;
}

/* 统一的效果块样式 */
.effect-block {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid #444;
  border-radius: 4px;
  padding: 8px 10px;
  margin: 8px 0;
}

.effect-label {
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
}

.effect-content {
  font-size: 13px;
  color: #fadb14; /* 亮黄色，匹配游戏常见的高亮色 */
  font-weight: 500;
  line-height: 1.5;
  white-space: pre-wrap;
}

.p-duration {
  font-size: 12px;
  color: #888;
  text-align: right;
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

.author {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  color: #bbb;
  display: none; /* 暂时隐藏，因为空间可能不够 */
}

@media (min-width: 1024px) {
  .author {
    display: flex;
  }
}

.author-link {
  color: #4dabf7;
  text-decoration: none;
}

.author-link:hover {
  color: #8bc6ff;
  text-decoration: underline;
}
</style>
