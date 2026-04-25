import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useMortalStore } from '@/stores/mortal'
import {
  formatPopulationGrowthText,
  formatPopulationText,
} from '@/utils/populationFormat'

export function useMortalOverviewModal(show: () => boolean) {
  const { locale, t } = useI18n()
  const mortalStore = useMortalStore()
  const mortalTheme = SYSTEM_PANEL_THEMES.mortal
  const panelStyleVars = {
    '--panel-accent': mortalTheme.accent,
    '--panel-accent-strong': mortalTheme.accentStrong,
    '--panel-accent-soft': mortalTheme.accentSoft,
    '--panel-title': mortalTheme.title,
    '--panel-empty': mortalTheme.empty,
    '--panel-border': mortalTheme.border,
    '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
    '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
  }

  const summary = computed(() => mortalStore.overview.summary)
  const cityRows = computed(() => mortalStore.overview.cities)
  const trackedMortals = computed(() => mortalStore.overview.tracked_mortals)

  function formatPopulation(value: number): string {
    return formatPopulationText(value, t, locale.value)
  }

  function formatNaturalGrowth(value: number): string {
    return formatPopulationGrowthText(value, t, locale.value)
  }

  function resolveBirthRegion(name: string): string {
    return name || t('game.mortal_system.tracked.unknown_region')
  }

  watch(
    show,
    (isShown) => {
      if (isShown) {
        void mortalStore.refreshOverview()
      }
    },
  )

  return {
    mortalStore,
    panelStyleVars,
    summary,
    cityRows,
    trackedMortals,
    formatPopulation,
    formatNaturalGrowth,
    resolveBirthRegion,
  }
}
