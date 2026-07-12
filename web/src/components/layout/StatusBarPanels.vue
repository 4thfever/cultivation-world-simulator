<script setup lang="ts">
import { computed, defineAsyncComponent, ref } from 'vue'
import type { Component } from 'vue'

import { useAvatarOverviewStore } from '@/stores/avatarOverview'
import PhenomenonSelectorModal from '@/components/game/panels/PhenomenonSelectorModal.vue'

const RankingModal = defineAsyncComponent(() => import('@/components/game/panels/RankingModal.vue'))
const TournamentModal = defineAsyncComponent(() => import('@/components/game/panels/TournamentModal.vue'))
const SectRelationsModal = defineAsyncComponent(() => import('@/components/game/panels/SectRelationsModal.vue'))
const MortalOverviewModal = defineAsyncComponent(() => import('@/components/game/panels/MortalOverviewModal.vue'))
const DynastyOverviewModal = defineAsyncComponent(() => import('@/components/game/panels/DynastyOverviewModal.vue'))
const HiddenDomainOverviewModal = defineAsyncComponent(() => import('@/components/game/panels/HiddenDomainOverviewModal.vue'))
const WorldInfoModal = defineAsyncComponent(() => import('@/components/game/panels/WorldInfoModal.vue'))
const TimeOverviewModal = defineAsyncComponent(() => import('@/components/game/panels/TimeOverviewModal.vue'))
const AvatarOverviewModal = defineAsyncComponent(() => import('@/components/game/panels/AvatarOverviewModal.vue'))
const WorldSecretModal = defineAsyncComponent(() => import('@/components/game/panels/WorldSecretModal.vue'))

type StatusBarPanelKey =
  | 'time'
  | 'worldInfo'
  | 'ranking'
  | 'tournament'
  | 'sectRelations'
  | 'mortalOverview'
  | 'dynastyOverview'
  | 'hiddenDomain'
  | 'phenomenonSelector'
  | 'avatarOverview'
  | 'worldSecret'

const avatarOverviewStore = useAvatarOverviewStore()

type StatusBarPanelDefinition = {
  component: Component
  beforeOpen?: () => Promise<void> | void
}

const panelRegistry: Record<StatusBarPanelKey, StatusBarPanelDefinition> = {
  time: { component: TimeOverviewModal },
  worldInfo: { component: WorldInfoModal },
  ranking: { component: RankingModal },
  tournament: { component: TournamentModal },
  sectRelations: { component: SectRelationsModal },
  mortalOverview: { component: MortalOverviewModal },
  dynastyOverview: { component: DynastyOverviewModal },
  hiddenDomain: { component: HiddenDomainOverviewModal },
  phenomenonSelector: { component: PhenomenonSelectorModal },
  avatarOverview: {
    component: AvatarOverviewModal,
    async beforeOpen() {
      if (!avatarOverviewStore.isLoaded) {
        await avatarOverviewStore.refreshOverview()
      }
    },
  },
  worldSecret: { component: WorldSecretModal },
}

const activePanel = ref<StatusBarPanelKey | null>(null)
const activePanelDefinition = computed(() => (
  activePanel.value ? panelRegistry[activePanel.value] : null
))

function closeActivePanel() {
  activePanel.value = null
}

async function open(panel: StatusBarPanelKey) {
  await panelRegistry[panel].beforeOpen?.()
  activePanel.value = panel
}

defineExpose({ open })
</script>

<template>
  <component
    :is="activePanelDefinition.component"
    v-if="activePanelDefinition"
    :show="true"
    @update:show="value => { if (!value) closeActivePanel() }"
  />
</template>
