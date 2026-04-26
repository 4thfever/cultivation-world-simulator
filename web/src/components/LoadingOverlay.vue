<script setup lang="ts">
import type { InitStatusDTO } from '../api'
import { useI18n } from 'vue-i18n'
import { useLoadingOverlayState } from '@/composables/useLoadingOverlayState'
import refreshIcon from '@/assets/icons/ui/lucide/refresh-cw.svg'
import triangleAlertIcon from '@/assets/icons/ui/lucide/triangle-alert.svg'

const { t } = useI18n()

const props = defineProps<{
  status: InitStatusDTO | null
}>()

const {
  currentTip,
  progress,
  phaseText,
  isError,
  errorMessage,
  bgOpacity,
  localElapsed,
  radius,
  circumference,
  strokeDashoffset,
  handleRetry,
} = useLoadingOverlayState(() => props.status)
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
            <span
              v-if="isError"
              class="ring-error-icon"
              :style="{ '--icon-url': `url(${triangleAlertIcon})` }"
              aria-hidden="true"
            ></span>
            <template v-else>{{ progress + '%' }}</template>
          </div>
        </div>
      </div>

      <div class="phase-text">{{ isError ? t('loading.error') : phaseText }}</div>

      <!-- 错误信息 -->
      <div v-if="isError" class="error-section">
        <p class="error-message">{{ errorMessage }}</p>
        <button class="retry-btn" @click="handleRetry">
          <span class="retry-icon" :style="{ '--icon-url': `url(${refreshIcon})` }" aria-hidden="true"></span>
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
  margin-top: 18px;
  letter-spacing: 2px;
  text-align: center;
  max-width: min(320px, 80vw);
  line-height: 1.5;
  min-height: 1.5em;
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.retry-btn:hover {
  background: rgba(255, 107, 107, 0.1);
  border-color: rgba(255, 107, 107, 0.6);
}

.ring-error-icon,
.retry-icon {
  display: inline-block;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
  flex-shrink: 0;
}

.ring-error-icon {
  width: 48px;
  height: 48px;
}

.retry-icon {
  width: 1em;
  height: 1em;
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
