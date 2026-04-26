import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useUiStore } from '@/stores/ui'
import type { SectRelationDTO } from '@/types/api'
import { useWorldOverviewData } from '@/composables/useWorldOverviewData'

export function useSectRelationsModal(show: () => boolean, close: () => void) {
  const { t } = useI18n()
  const uiStore = useUiStore()
  const sectTheme = SYSTEM_PANEL_THEMES.sectRelations
  const panelStyleVars = {
    '--panel-accent': sectTheme.accent,
    '--panel-accent-strong': sectTheme.accentStrong,
    '--panel-accent-soft': sectTheme.accentSoft,
    '--panel-link': sectTheme.link,
    '--panel-link-hover': sectTheme.linkHover,
    '--panel-title': sectTheme.title,
    '--panel-empty': sectTheme.empty,
    '--panel-border': sectTheme.border,
    '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
    '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
  }

  const { loading, relations, fetchRelations } = useWorldOverviewData('SectRelationsModal')
  const sortedRelations = computed(() => [...relations.value].sort((a, b) => a.value - b.value))

  function getValueColor(value: number) {
    if (value <= -50) return SHARED_UI_COLORS.dangerSoft
    if (value < 0) return '#d8a14a'
    if (value >= 50) return SHARED_UI_COLORS.successSoft
    if (value > 0) return '#b6df89'
    return '#d9d9d9'
  }

  function getDeltaColor(delta: number) {
    if (delta > 0) return SHARED_UI_COLORS.successStrong
    if (delta < 0) return SHARED_UI_COLORS.dangerStrong
    return '#d9d9d9'
  }

  function formatDelta(delta: number): string {
    if (delta > 0) return `+${delta}`
    return `${delta}`
  }

  function getValueLabelKey(value: number): string {
    if (value <= -50) return 'value_label_very_hostile'
    if (value < 0) return 'value_label_hostile'
    if (value === 0) return 'value_label_neutral'
    if (value < 50) return 'value_label_friendly'
    return 'value_label_very_friendly'
  }

  function resolveReasonLabel(item: SectRelationDTO['reason_breakdown'][number]) {
    const baseLabel = t(`game.sect_relations.reasons_map.${item.reason}`)
    if (item.reason === 'PEACE_STATE') return ''
    if (item.reason === 'LONG_PEACE') return baseLabel
    if (item.reason === 'RANDOM_EVENT') {
      const cause = item.meta?.cause
      return typeof cause === 'string' && cause.trim() ? `${baseLabel} (${cause.trim()})` : baseLabel
    }

    if (item.reason !== 'TERRITORY_CONFLICT') {
      if (item.reason === 'WAR_STATE' || item.reason === 'PEACE_STATE' || item.reason === 'LONG_PEACE') {
        const months = item.meta?.war_months ?? item.meta?.peace_months
        if (typeof months === 'number' && months > 0) {
          return `${baseLabel} (${t('game.sect_relations.duration_months', { count: months })})`
        }
      }
      return baseLabel
    }

    const borderContactEdges = item.meta?.border_contact_edges ?? item.meta?.overlap_tiles
    if (typeof borderContactEdges !== 'number') return baseLabel
    return `${baseLabel} (${t('game.sect_relations.overlap_tiles', { count: borderContactEdges })})`
  }

  function resolveDiplomacyStatus(item: SectRelationDTO) {
    const key = item.diplomacy_status === 'war'
      ? 'game.sect_relations.status_war'
      : 'game.sect_relations.status_peace'
    return `${t(key)} · ${t('game.sect_relations.duration_months', { count: item.diplomacy_duration_months })}`
  }

  function openSectInfo(id: number) {
    void uiStore.select('sect', String(id))
    close()
  }

  watch(show, (isShown) => {
    if (isShown) {
      void fetchRelations()
    }
  }, { immediate: true })

  return {
    loading,
    panelStyleVars,
    sortedRelations,
    getValueColor,
    getDeltaColor,
    formatDelta,
    getValueLabelKey,
    resolveReasonLabel,
    resolveDiplomacyStatus,
    openSectInfo,
  }
}
