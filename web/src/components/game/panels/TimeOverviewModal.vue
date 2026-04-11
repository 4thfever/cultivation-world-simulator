<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { NModal, NSpin } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { worldApi } from '@/api/modules/world'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useWorldStore } from '@/stores/world'
import type { RankingsDTO, SectRelationDTO } from '@/types/api'
import calendarIcon from '@/assets/icons/ui/lucide/calendar.svg'
import sparklesIcon from '@/assets/icons/ui/lucide/sparkles.svg'
import swordsIcon from '@/assets/icons/ui/lucide/swords.svg'
import shieldIcon from '@/assets/icons/ui/lucide/shield.svg'
import { logError } from '@/utils/appError'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()
const worldStore = useWorldStore()
const timeTheme = SYSTEM_PANEL_THEMES.time
const panelStyleVars = {
  '--panel-accent': timeTheme.accent,
  '--panel-accent-strong': timeTheme.accentStrong,
  '--panel-accent-soft': timeTheme.accentSoft,
  '--panel-title': timeTheme.title,
  '--panel-empty': timeTheme.empty,
  '--panel-border': timeTheme.border,
  '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
  '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
  '--panel-text-muted': SHARED_UI_COLORS.textMuted,
}

const loading = ref(false)
const rankings = ref<RankingsDTO>({
  heaven: [],
  earth: [],
  human: [],
  sect: [],
})
const relations = ref<SectRelationDTO[]>([])

const currentDateText = computed(() => (
  t('game.status_bar.time.current_date_value', {
    year: worldStore.year,
    month: worldStore.month,
  })
))

const elapsedTimeText = computed(() => {
  const totalMonths = worldStore.elapsedMonths
  const years = Math.floor(totalMonths / 12)
  const months = totalMonths % 12

  if (years <= 0) {
    return t('game.status_bar.time.elapsed_months_only', { months: totalMonths })
  }

  if (months === 0) {
    return t('game.status_bar.time.elapsed_years_only', { years })
  }

  return t('game.status_bar.time.elapsed_years_months', { years, months })
})

const phenomenonName = computed(() => (
  worldStore.currentPhenomenon?.name || t('game.status_bar.time.no_phenomenon')
))

const nextTournamentText = computed(() => {
  const nextYear = rankings.value.tournament?.next_year ?? 0
  if (nextYear <= 0) {
    return t('game.status_bar.time.no_tournament')
  }

  return t('game.ranking.tournament_next', {
    years: Math.max(0, nextYear - worldStore.year),
  })
})

const warCount = computed(() => (
  relations.value.filter(item => item.diplomacy_status === 'war').length
))

const warStatusText = computed(() => (
  warCount.value > 0
    ? t('game.status_bar.time.war_active', { count: warCount.value })
    : t('game.status_bar.time.war_none')
))

async function fetchTimeOverviewData() {
  loading.value = true
  try {
    const [rankingsResult, relationsResult] = await Promise.allSettled([
      worldApi.fetchRankings(),
      worldApi.fetchSectRelations(),
    ])

    if (rankingsResult.status === 'fulfilled') {
      rankings.value = rankingsResult.value
    } else {
      rankings.value = { heaven: [], earth: [], human: [], sect: [] }
      logError('TimeOverviewModal fetch rankings', rankingsResult.reason)
    }

    if (relationsResult.status === 'fulfilled') {
      relations.value = relationsResult.value.relations ?? []
    } else {
      relations.value = []
      logError('TimeOverviewModal fetch sect relations', relationsResult.reason)
    }
  } finally {
    loading.value = false
  }
}

function handleShowChange(value: boolean) {
  emit('update:show', value)
}

watch(
  () => props.show,
  (show) => {
    if (show) {
      void fetchTimeOverviewData()
    }
  },
)
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
