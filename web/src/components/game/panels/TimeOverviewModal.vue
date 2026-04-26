<script setup lang="ts">
import { NModal, NSpin } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useTimeOverviewModal } from '@/composables/useTimeOverviewModal'
import calendarIcon from '@/assets/icons/ui/lucide/calendar.svg'
import sparklesIcon from '@/assets/icons/ui/lucide/sparkles.svg'
import swordsIcon from '@/assets/icons/ui/lucide/swords.svg'
import shieldIcon from '@/assets/icons/ui/lucide/shield.svg'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()
const {
  loading,
  panelStyleVars,
  currentDateText,
  elapsedTimeText,
  phenomenonName,
  nextTournamentText,
  warStatusText,
} = useTimeOverviewModal(() => props.show)

function handleShowChange(value: boolean) {
  emit('update:show', value)
}
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.status_bar.time.title')"
    style="width: 520px; max-height: 80vh; overflow-y: auto;"
  >
    <n-spin :show="loading">
      <div class="time-overview" :style="panelStyleVars">
        <section class="time-hero">
          <div class="hero-label">{{ t('game.status_bar.time.current_date') }}</div>
          <div class="hero-value">{{ currentDateText }}</div>
        </section>

        <div class="time-grid">
          <article class="time-card">
            <div class="card-label">
              <span class="card-icon" :style="{ '--icon-url': `url(${calendarIcon})` }" aria-hidden="true"></span>
              {{ t('game.status_bar.time.elapsed') }}
            </div>
            <div class="card-value">{{ elapsedTimeText }}</div>
          </article>

          <article class="time-card">
            <div class="card-label">
              <span class="card-icon" :style="{ '--icon-url': `url(${sparklesIcon})` }" aria-hidden="true"></span>
              {{ t('game.status_bar.time.phenomenon') }}
            </div>
            <div class="card-value">{{ phenomenonName }}</div>
          </article>

          <article class="time-card">
            <div class="card-label">
              <span class="card-icon" :style="{ '--icon-url': `url(${swordsIcon})` }" aria-hidden="true"></span>
              {{ t('game.status_bar.time.tournament') }}
            </div>
            <div class="card-value">{{ nextTournamentText }}</div>
          </article>

          <article class="time-card">
            <div class="card-label">
              <span class="card-icon" :style="{ '--icon-url': `url(${shieldIcon})` }" aria-hidden="true"></span>
              {{ t('game.status_bar.time.sect_war') }}
            </div>
            <div class="card-value">{{ warStatusText }}</div>
          </article>
        </div>
      </div>
    </n-spin>
  </n-modal>
</template>

<style scoped>
.time-overview {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.time-hero {
  padding: 14px 16px;
  border: 1px solid var(--panel-border);
  border-radius: 10px;
  background:
    linear-gradient(180deg, rgba(210, 197, 163, 0.14), rgba(210, 197, 163, 0.06)),
    rgba(255, 255, 255, 0.02);
}

.hero-label {
  font-size: 13px;
  color: var(--panel-text-secondary);
  margin-bottom: 6px;
}

.hero-value {
  font-size: 24px;
  line-height: 1.2;
  color: var(--panel-title);
  font-weight: 700;
  letter-spacing: 0.02em;
  font-variant-numeric: tabular-nums;
}

.time-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.time-card {
  min-width: 0;
  padding: 12px 14px;
  border: 1px solid var(--panel-border);
  border-radius: 10px;
  background: var(--panel-accent-soft);
}

.card-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  color: var(--panel-text-secondary);
  font-size: 13px;
}

.card-value {
  color: var(--panel-text-primary);
  line-height: 1.5;
  font-weight: 700;
}

.card-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
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
}

@media (max-width: 640px) {
  .time-grid {
    grid-template-columns: 1fr;
  }
}
</style>
