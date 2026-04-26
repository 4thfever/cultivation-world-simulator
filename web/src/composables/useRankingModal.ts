import { watch } from 'vue'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useUiStore } from '@/stores/ui'
import { useWorldOverviewData } from '@/composables/useWorldOverviewData'

export function useRankingModal(show: () => boolean, close: () => void) {
  const uiStore = useUiStore()
  const rankingTheme = SYSTEM_PANEL_THEMES.ranking
  const panelStyleVars = {
    '--panel-accent': rankingTheme.accent,
    '--panel-accent-strong': rankingTheme.accentStrong,
    '--panel-accent-soft': rankingTheme.accentSoft,
    '--panel-link': rankingTheme.link,
    '--panel-link-hover': rankingTheme.linkHover,
    '--panel-title': rankingTheme.title,
    '--panel-empty': rankingTheme.empty,
    '--panel-border': rankingTheme.border,
    '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
    '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
    '--panel-text-muted': SHARED_UI_COLORS.textMuted,
  }

  const { loading, rankings, fetchRankings } = useWorldOverviewData('RankingModal')

  function openAvatarInfo(id: string) {
    void uiStore.select('avatar', id)
    close()
  }

  function openSectInfo(id: string) {
    void uiStore.select('sect', id)
    close()
  }

  watch(show, (isShown) => {
    if (isShown) {
      void fetchRankings()
    }
  }, { immediate: true })

  return {
    loading,
    rankings,
    panelStyleVars,
    openAvatarInfo,
    openSectInfo,
  }
}
