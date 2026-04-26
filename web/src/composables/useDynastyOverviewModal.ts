import { computed, watch } from 'vue'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useDynastyStore } from '@/stores/dynasty'
import { useUiStore } from '@/stores/ui'

export function useDynastyOverviewModal(show: () => boolean) {
  const dynastyStore = useDynastyStore()
  const uiStore = useUiStore()
  const dynastyTheme = SYSTEM_PANEL_THEMES.dynasty
  const panelStyleVars = {
    '--panel-accent': dynastyTheme.accent,
    '--panel-accent-strong': dynastyTheme.accentStrong,
    '--panel-accent-soft': dynastyTheme.accentSoft,
    '--panel-title': dynastyTheme.title,
    '--panel-empty': dynastyTheme.empty,
    '--panel-border': dynastyTheme.border,
    '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
    '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
  }

  const overview = computed(() => dynastyStore.overview)
  const officials = computed(() => dynastyStore.officials)
  const summary = computed(() => dynastyStore.summary)
  const hasOverview = computed(() => Boolean(overview.value.name))
  const emperor = computed(() => overview.value.current_emperor)
  const effectLines = computed(() => {
    const text = overview.value.effect_desc || ''
    if (!text) return []
    return text.split(/[;\n；]/).map((line) => line.trim()).filter(Boolean)
  })

  function jumpToAvatar(id: string) {
    void uiStore.select('avatar', id)
  }

  watch(
    show,
    (isShown) => {
      if (isShown) {
        void dynastyStore.refreshDetail()
      }
    },
    { immediate: true },
  )

  return {
    dynastyStore,
    panelStyleVars,
    overview,
    officials,
    summary,
    hasOverview,
    emperor,
    effectLines,
    jumpToAvatar,
  }
}
