import { computed } from 'vue'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useWorldStore } from '@/stores/world'

export function useHiddenDomainOverviewModal() {
  const worldStore = useWorldStore()
  const hiddenDomainTheme = SYSTEM_PANEL_THEMES.hiddenDomain
  const panelStyleVars = {
    '--panel-accent': hiddenDomainTheme.accent,
    '--panel-accent-strong': hiddenDomainTheme.accentStrong,
    '--panel-accent-soft': hiddenDomainTheme.accentSoft,
    '--panel-title': hiddenDomainTheme.title,
    '--panel-empty': hiddenDomainTheme.empty,
    '--panel-border': hiddenDomainTheme.border,
    '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
    '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
  }

  const domainItems = computed(() => worldStore.activeDomains)

  function formatPercent(value: number): string {
    return `${(value * 100).toFixed(0)}%`
  }

  return {
    panelStyleVars,
    domainItems,
    formatPercent,
  }
}
