<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { systemApi, type InitStatusDTO } from '../api'
import { useI18n } from 'vue-i18n'

const { t, tm } = useI18n()

const props = defineProps<{
  status: InitStatusDTO | null
}>()

const tipsList = computed<string[]>(() => {
  const list = (tm as any)('loading.tips')
  return Array.isArray(list) ? list : []
})

const currentTip = ref('')
const displayProgress = ref(0) // 实际显示的进度
const localElapsed = ref(0)
let tipInterval: ReturnType<typeof setInterval> | null = null
let elapsedInterval: ReturnType<typeof setInterval> | null = null

const progress = computed(() => displayProgress.value)
const phaseText = computed(() => {
  const phaseName = props.status?.phase_name || ''
  if (!phaseName) return t('loading.phase.chaos')
  return t(`loading.phase.${phaseName}`)
})
const isError = computed(() => props.status?.status === 'error')
const errorMessage = computed(() => props.status?.error || t('loading.unknown_error'))

// 初始化随机 Tip
watch(tipsList, (list) => {
  if (list.length > 0 && !currentTip.value) {
    currentTip.value = list[Math.floor(Math.random() * list.length)]
  }
}, { immediate: true })

// 监听后端进度，如果后端进度领先，则同步
watch(() => props.status?.progress, (newVal) => {
  if (newVal !== undefined && newVal !== null) {
    if (newVal > displayProgress.value) {
      displayProgress.value = newVal
    }
  }
}, { immediate: true })

// 根据时间计算背景透明度：前5秒保持不透明，5-20秒逐渐透明到0.8。
// 只影响背景，不影响内容亮度。
const bgOpacity = computed(() => {
  const elapsed = localElapsed.value
  if (elapsed <= 5) return 1
  if (elapsed >= 20) return 0.9
  // 5秒 -> 1.0, 20秒 -> 0.9 (线性插值)。
  return 1 - (elapsed - 5) / 15 * 0.1
})

// SVG 圆环参数
const radius = 90
const circumference = 2 * Math.PI * radius
const strokeDashoffset = computed(() => {
  return circumference - (progress.value / 100) * circumference
})

async function handleRetry() {
  localElapsed.value = 0
  displayProgress.value = 0
  try {
    await systemApi.reinitGame()
  } catch (e: any) {
    console.error('Reinit failed:', e)
  }
}

function startTimers() {
  // Tips 切换
  tipInterval = setInterval(() => {
    if (tipsList.value.length > 0) {
      const idx = Math.floor(Math.random() * tipsList.value.length)
      currentTip.value = tipsList.value[idx]
    }
  }, 5000)
  
  // 本地计时器 + 阶段文案轮换 + 伪进度自增
  elapsedInterval = setInterval(() => {
    localElapsed.value++

    // 伪进度逻辑
    if (props.status?.status === 'in_progress' && displayProgress.value < 99) {
      const currentPhase = props.status?.phase ?? 0
      // 后端定义的进度节点: {0: 0, 1: 10, 2: 25, 3: 40, 4: 55, 5: 70, 6: 85}
      const progressMap: Record<number, number> = { 0: 0, 1: 10, 2: 25, 3: 40, 4: 55, 5: 70, 6: 85 }
      const nextPhaseStart = progressMap[currentPhase + 1] ?? 100
      
      // 每1秒增加 1%
      if (localElapsed.value % 1 === 0) {
        // 如果还没达到下一阶段的起点前 1%，就继续自增
        if (displayProgress.value < nextPhaseStart - 1) {
          displayProgress.value++
        } else if (currentPhase === 6 && displayProgress.value < 99) {
          // 最后一个阶段（6阶段）允许一直增加到 99%
          displayProgress.value++
        }
      }
    }
  }, 1000)
}

function stopTimers() {
  if (tipInterval) {
    clearInterval(tipInterval)
    tipInterval = null
  }
  if (elapsedInterval) {
    clearInterval(elapsedInterval)
    elapsedInterval = null
  }
}

// 当状态从 ready 变成其他时，重置
watch(() => props.status?.status, (newStatus, oldStatus) => {
  if (oldStatus === 'ready' && newStatus !== 'ready') {
    localElapsed.value = 0
    displayProgress.value = 0
  }
})

onMounted(() => {
  startTimers()
})

onUnmounted(() => {
  stopTimers()
})
</script>

<template>
  <div class="loading-overlay">
    <!-- 背景层 - 只有这层透明度变化 -->
    <div 
      class="bg-layer"
      :style="{ opacity: bgOpacity }"
    ></div>

    <!-- 背景装饰 -->
    <div class="bg-decoration" :style="{ opacity: bgOpacity }">
      <div class="glow glow-1"></div>
      <div class="glow glow-2"></div>
    </div>

    <!-- 主内容 -->
    <div class="content">
      <!-- 标题 -->
      <h1 class="title">{{ t('loading.title') }}</h1>
      <p class="subtitle">{{ t('loading.subtitle') }}</p>

      <!-- 进度圆环 -->
      <div class="progress-ring">
        <svg width="220" height="220" viewBox="0 0 220 220">
          <defs>
            <linearGradient id="progress-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#00d4ff;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#00ffa3;stop-opacity:1" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <!-- 背景圆环 -->
          <circle
            class="track"
            cx="110"
            cy="110"
            :r="radius"
          />
          <!-- 进度圆环 -->
          <circle
            class="progress"
            :class="{ error: isError }"
            cx="110"
            cy="110"
            :r="radius"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="strokeDashoffset"
            filter="url(#glow)"
          />
        </svg>
        
        <!-- 圆环内容 -->
        <div class="ring-content">
          <div class="percentage" :class="{ error: isError }">
            {{ isError ? '!' : progress + '%' }}
          </div>
          <div class="phase-text">{{ isError ? t('loading.error') : phaseText }}</div>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="isError" class="error-section">
        <p class="error-message">{{ errorMessage }}</p>
        <button class="retry-btn" @click="handleRetry">
          {{ t('loading.retry') }}
        </button>
      </div>

      <!-- Tips -->
      <div v-else class="tips-section">
        <div class="tips-label">{{ t('loading.tips_label') }}</div>
        <div class="tips">{{ currentTip }}</div>
      </div>
    </div>

    <!-- 底部信息 -->
    <div class="footer">
      <div class="elapsed">{{ t('loading.elapsed', { seconds: localElapsed }) }}</div>
      <div class="version" v-if="props.status?.version">{{ t('common.version', 'Version') }} v{{ props.status.version }}</div>
    </div>
  </div>
</template>

<style scoped>
.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* 背景层 - 只有这层会变透明，带模糊效果 */
.bg-layer {
  position: absolute;
  inset: 0;
  background: rgba(10, 10, 18, 0.98);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: opacity 0.5s ease;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
}

.glow-1 {
  width: 400px;
  height: 400px;
  background: #00d4ff;
  top: 10%;
  left: 20%;
  animation: float 8s ease-in-out infinite;
}

.glow-2 {
  width: 300px;
  height: 300px;
  background: #00ffa3;
  bottom: 20%;
  right: 15%;
  animation: float 6s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, -20px); }
}

/* 主内容 */
.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
}

.title {
  font-size: 42px;
  font-weight: 300;
  letter-spacing: 16px;
  margin: 0 0 8px 16px;
  background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.8) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 12px;
  letter-spacing: 4px;
  color: rgba(255, 255, 255, 0.3);
  margin: 0 0 50px 0;
  text-transform: uppercase;
}

/* 进度圆环 */
.progress-ring {
  width: 220px;
  height: 220px;
  position: relative;
}

.progress-ring svg {
  transform: rotate(-90deg);
}

.progress-ring circle.track {
  fill: none;
  stroke: rgba(255, 255, 255, 0.06);
  stroke-width: 4;
}

.progress-ring circle.progress {
  fill: none;
  stroke: url(#progress-gradient);
  stroke-width: 4;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.5s ease;
}

.progress-ring circle.progress.error {
  stroke: #ff6b6b;
}

.ring-content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.percentage {
  font-size: 48px;
  font-weight: 200;
  color: #fff;
  letter-spacing: 2px;
}

.percentage.error {
  color: #ff6b6b;
  font-size: 56px;
}

.phase-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 8px;
  letter-spacing: 2px;
}

/* 错误区域 */
.error-section {
  margin-top: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.error-message {
  color: rgba(255, 107, 107, 0.9);
  font-size: 14px;
  max-width: 300px;
  text-align: center;
  margin: 0;
}

.retry-btn {
  padding: 12px 32px;
  background: transparent;
  border: 1px solid rgba(255, 107, 107, 0.4);
  border-radius: 24px;
  color: rgba(255, 107, 107, 0.9);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 1px;
}

.retry-btn:hover {
  background: rgba(255, 107, 107, 0.1);
  border-color: rgba(255, 107, 107, 0.6);
}

/* Tips 区域 */
.tips-section {
  margin-top: 50px;
  text-align: center;
}

.tips-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.25);
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.tips {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.45);
  max-width: 300px;
  line-height: 1.6;
  transition: opacity 0.3s ease;
}

/* 底部 */
.footer {
  position: absolute;
  bottom: 24px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  padding: 0 32px;
}

.elapsed, .version {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.2);
  letter-spacing: 1px;
}
</style>
