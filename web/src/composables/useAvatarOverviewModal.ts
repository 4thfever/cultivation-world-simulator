import { computed, ref, watch } from 'vue'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useAvatarOverviewStore } from '@/stores/avatarOverview'
import { useDeceasedRecords } from '@/composables/useDeceasedRecords'

export function useAvatarOverviewModal(show: () => boolean) {
  const avatarOverviewStore = useAvatarOverviewStore()
  const avatarTheme = SYSTEM_PANEL_THEMES.dynasty
  const panelStyleVars = {
    '--panel-accent': avatarTheme.accent,
    '--panel-accent-strong': avatarTheme.accentStrong,
    '--panel-accent-soft': avatarTheme.accentSoft,
    '--panel-title': avatarTheme.title,
    '--panel-empty': avatarTheme.empty,
    '--panel-border': avatarTheme.border,
    '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
    '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
  }

  const summary = computed(() => avatarOverviewStore.overview.summary)
  const realmDistribution = computed(() => avatarOverviewStore.overview.realmDistribution)
  const activeTab = ref<'overview' | 'deceased'>('overview')
  const {
    recordsLoading: deceasedLoading,
    recordsLoaded: deceasedLoaded,
    records,
    selectedRecord,
    eventsLoading,
    events,
    fetchRecords: fetchDeceased,
    selectRecord,
    backToList,
    resetSelection,
  } = useDeceasedRecords({ logScope: 'AvatarOverviewModal' })

  async function handleTabUpdate(value: string) {
    activeTab.value = value === 'deceased' ? 'deceased' : 'overview'
    if (activeTab.value === 'deceased' && !deceasedLoaded.value) {
      await fetchDeceased()
    }
  }

  watch(
    show,
    (isShown) => {
      if (isShown) {
        activeTab.value = 'overview'
        resetSelection()
        void avatarOverviewStore.refreshOverview()
        return
      }

      activeTab.value = 'overview'
      resetSelection()
    },
    { immediate: true },
  )

  return {
    avatarOverviewStore,
    panelStyleVars,
    summary,
    realmDistribution,
    activeTab,
    deceasedLoading,
    records,
    selectedRecord,
    eventsLoading,
    events,
    selectRecord,
    backToList,
    handleTabUpdate,
  }
}
