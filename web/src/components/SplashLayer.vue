<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NButton, NSpace } from 'naive-ui'

// 定义事件
const emit = defineEmits<{
  (e: 'action', key: string): void
}>()

const videoRef = ref<HTMLVideoElement | null>(null)

// 视频播放控制逻辑
onMounted(() => {
  if (!videoRef.value) return
  videoRef.value.playbackRate = 0.8
})

// 定义按钮列表
const menuOptions = [
  { label: '开始游戏', subLabel: 'Start Game', key: 'start', disabled: false },
  { label: '加载游戏', subLabel: 'Load Game', key: 'load', disabled: false },
  { label: '成就', subLabel: 'Achievements', key: 'achievements', disabled: true },
  { label: '设置', subLabel: 'Settings', key: 'settings', disabled: true },
  { label: '离开', subLabel: 'Exit', key: 'exit', disabled: false }
]

function handleClick(key: string) {
  emit('action', key)
}
</script>

<template>
  <div class="splash-container">
    <video
      ref="videoRef"
      class="splash-video"
      autoplay
      muted
      loop
      playsinline
      :poster="'/assets/splash.png'"
    >
      <source :src="'/assets/splash.mp4'" type="video/mp4" />
    </video>
    <!-- 左侧模糊层 -->
    <div class="glass-panel">
      <div class="title-area">
        <h1>修仙模拟器</h1>
        <p>Cultivation World Simulator</p>
      </div>
      
      <div class="menu-area">
        <n-space vertical size="large">
          <n-button
            v-for="opt in menuOptions"
            :key="opt.key"
            size="large"
            block
            color="#ffffff20"
            text-color="#fff"
            class="menu-btn"
            :disabled="opt.disabled"
            @click="handleClick(opt.key)"
          >
            <div class="btn-content">
              <span class="btn-label">{{ opt.label }}</span>
              <span class="btn-sub">{{ opt.subLabel }}</span>
            </div>
          </n-button>
        </n-space>
      </div>
    </div>
  </div>
</template>

<style scoped>
.splash-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  display: flex;
  align-items: center;
  background-color: #000; /* 视频加载前的底色 */
  overflow: hidden;
}

.splash-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
}

/* 左侧毛玻璃面板 */
.glass-panel {
  position: relative;
  z-index: 1;
  width: 400px;
  height: 100%;
  background: rgba(0, 0, 0, 0.4); /* 半透明黑底 */
  backdrop-filter: blur(20px); /* 核心模糊效果 */
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 60px;
  box-shadow: 10px 0 30px rgba(0, 0, 0, 0.5);
}

.title-area {
  margin-bottom: 80px;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

.title-area h1 {
  font-size: 3rem;
  margin-bottom: 10px;
  font-weight: bold;
  letter-spacing: 4px;
}

.title-area p {
  font-size: 1.2rem;
  opacity: 0.8;
  letter-spacing: 2px;
}

/* 按钮样式微调 */
.menu-btn {
  height: 60px; /* 稍微加大一点按钮高度 */
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  
  /* 核心修复：强制内容左对齐 */
  justify-content: flex-start;
  text-align: left;
  padding-left: 32px; /* 统一的左侧留白 */
}

/* 修复 Naive UI 按钮内容可能默认居中的问题 */
.menu-btn :deep(.n-button__content) {
  justify-content: flex-start;
  width: 100%;
}

.btn-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start; /* 左对齐 */
  width: 100%;
}

.btn-label {
  font-size: 20px;
  letter-spacing: 4px;
  line-height: 1.2;
}

.btn-sub {
  font-size: 10px;
  opacity: 0.6;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.menu-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateX(10px);
  box-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
}

/* 针对移动端的简单适配（虽然这种游戏一般是桌面端） */
@media (max-width: 768px) {
  .glass-panel {
    width: 100%;
    border-right: none;
    background: rgba(0, 0, 0, 0.6);
  }
}
</style>
