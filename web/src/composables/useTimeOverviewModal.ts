import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useWorldStore } from '@/stores/world'
import { useWorldOverviewData } from '@/composables/useWorldOverviewData'

export function useTimeOverviewModal(show: () => boolean) {
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

  const {
    loading,
    rankings,
    relations,
    fetchRankingsAndRelations,
  } = useWorldOverviewData('TimeOverviewModal')

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

    if (years <= 0) return t('game.status_bar.time.elapsed_months_only', { months: totalMonths })
    if (months === 0) return t('game.status_bar.time.elapsed_years_only', { years })
    return t('game.status_bar.time.elapsed_years_months', { years, months })
  })

  const phenomenonName = computed(() => (
    worldStore.currentPhenomenon?.name || t('game.status_bar.time.no_phenomenon')
  ))
  const nextTournamentText = computed(() => {
    const nextYear = rankings.value.tournament?.next_year ?? 0
    if (nextYear <= 0) return t('game.status_bar.time.no_tournament')
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

  watch(show, (isShown) => {
    if (isShown) {
      void fetchRankingsAndRelations()
    }
  }, { immediate: true })

  return {
    loading,
    panelStyleVars,
    currentDateText,
    elapsedTimeText,
    phenomenonName,
    nextTournamentText,
    warStatusText,
  }
}
