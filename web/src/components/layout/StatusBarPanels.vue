<script setup lang="ts">
import { defineAsyncComponent, ref } from 'vue'

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

const avatarOverviewStore = useAvatarOverviewStore()

const showPhenomenonSelector = ref(false)
const showTimeOverviewModal = ref(false)
const showWorldInfoModal = ref(false)
const showRankingModal = ref(false)
const showTournamentModal = ref(false)
const showSectRelationsModal = ref(false)
const showMortalOverviewModal = ref(false)
const showDynastyOverviewModal = ref(false)
const showHiddenDomainModal = ref(false)
const showAvatarOverviewModal = ref(false)

async function open(panel: StatusBarPanelKey) {
  if (panel === 'time') showTimeOverviewModal.value = true
  else if (panel === 'worldInfo') showWorldInfoModal.value = true
  else if (panel === 'ranking') showRankingModal.value = true
  else if (panel === 'tournament') showTournamentModal.value = true
  else if (panel === 'sectRelations') showSectRelationsModal.value = true
  else if (panel === 'mortalOverview') showMortalOverviewModal.value = true
  else if (panel === 'dynastyOverview') showDynastyOverviewModal.value = true
  else if (panel === 'hiddenDomain') showHiddenDomainModal.value = true
  else if (panel === 'phenomenonSelector') showPhenomenonSelector.value = true
  else if (panel === 'avatarOverview') {
    if (!avatarOverviewStore.isLoaded) {
      await avatarOverviewStore.refreshOverview()
    }
    showAvatarOverviewModal.value = true
  }
}

defineExpose({ open })
</script>

<template>
  <RankingModal v-if="showRankingModal" v-model:show="showRankingModal" />
  <TimeOverviewModal v-if="showTimeOverviewModal" v-model:show="showTimeOverviewModal" />
  <WorldInfoModal v-if="showWorldInfoModal" v-model:show="showWorldInfoModal" />
  <TournamentModal v-if="showTournamentModal" v-model:show="showTournamentModal" />
  <SectRelationsModal v-if="showSectRelationsModal" v-model:show="showSectRelationsModal" />
  <HiddenDomainOverviewModal v-if="showHiddenDomainModal" v-model:show="showHiddenDomainModal" />
  <MortalOverviewModal v-if="showMortalOverviewModal" v-model:show="showMortalOverviewModal" />
  <DynastyOverviewModal v-if="showDynastyOverviewModal" v-model:show="showDynastyOverviewModal" />
  <PhenomenonSelectorModal v-if="showPhenomenonSelector" v-model:show="showPhenomenonSelector" />
  <AvatarOverviewModal v-if="showAvatarOverviewModal" v-model:show="showAvatarOverviewModal" />
</template>
