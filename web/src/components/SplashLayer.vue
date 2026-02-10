<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { NButton, NSpace, NModal, NCard, NForm, NFormItem, NSelect } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useSettingStore } from '../stores/setting'
import { useBgm } from '../composables/useBgm'

// 定义事件
const emit = defineEmits<{
  (e: 'action', key: string): void
}>()

const { t } = useI18n()
const settingStore = useSettingStore()
const showSettings = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)

// 视频播放控制逻辑
onMounted(() => {
  // 播放背景音乐
  useBgm().play('splash')

  if (!videoRef.value) return
  
  const video = videoRef.value
  // 整体基础速度设为 0.8
  video.playbackRate = 0.8

  const handleTimeUpdate = () => {
    const duration = video.duration
    if (!duration) return

    const remaining = duration - video.currentTime
    
    // 当剩余时间小于 2 秒时开始线性减速
    if (remaining < 2 && remaining > 0) {
      // 从 0.8 逐渐降低，最低保持在 0.35 左右避免视觉卡顿感
      const targetRate = 0.35 + (0.8 - 0.35) * (remaining / 2)
      video.playbackRate = targetRate
    }
  }

  video.addEventListener('timeupdate', handleTimeUpdate)
})

const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: '繁體中文', value: 'zh-TW' },
  { label: 'English', value: 'en-US' }
]

// 定义按钮列表
const menuOptions = computed(() => [
  { label: t('ui.start_game'), subLabel: 'Start Game', key: 'start', disabled: false },
  { label: t('ui.load_game'), subLabel: 'Load Game', key: 'load', disabled: false },
  { label: t('ui.achievements'), subLabel: 'Achievements', key: 'achievements', disabled: true },
  { label: t('ui.settings'), subLabel: 'Settings', key: 'settings', disabled: false },
  { label: t('ui.exit'), subLabel: 'Exit', key: 'exit', disabled: false }
])

function handleClick(key: string) {
  if (key === 'settings') {
    showSettings.value = true
    return
  }
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
      playsinline
      :poster="'/assets/splash.png'"
    >
      <source :src="'/assets/splash.mp4'" type="video/mp4" />
    </video>
    <!-- 左侧模糊层 -->
    <div class="glass-panel">
      <div class="title-area">
        <h1>{{ t('splash.title') }}</h1>
        <p>AI Cultivation World Simulator</p>
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
            v-sound="'click'"
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

    <!-- Settings Modal -->
    <n-modal v-model:show="showSettings">
        <n-card
          style="width: 400px"
          :title="t('ui.settings')"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
        >
          <n-form>
            <n-form-item label="语言 / Language">
              <n-select
                v-model:value="settingStore.locale"
                :options="languageOptions"
                @update:value="settingStore.setLocale"
              />
            </n-form-item>
          </n-form>
        </n-card>
    </n-modal>
  </div>
</template>

<style scoped>
.splash-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 500;
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
