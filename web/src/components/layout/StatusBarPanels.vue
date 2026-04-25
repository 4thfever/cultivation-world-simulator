<script setup lang="ts">
import { ref } from 'vue'

import { useAvatarOverviewStore } from '@/stores/avatarOverview'
import RankingModal from '@/components/game/panels/RankingModal.vue'
import TournamentModal from '@/components/game/panels/TournamentModal.vue'
import SectRelationsModal from '@/components/game/panels/SectRelationsModal.vue'
import MortalOverviewModal from '@/components/game/panels/MortalOverviewModal.vue'
import DynastyOverviewModal from '@/components/game/panels/DynastyOverviewModal.vue'
import HiddenDomainOverviewModal from '@/components/game/panels/HiddenDomainOverviewModal.vue'
import WorldInfoModal from '@/components/game/panels/WorldInfoModal.vue'
import TimeOverviewModal from '@/components/game/panels/TimeOverviewModal.vue'
import PhenomenonSelectorModal from '@/components/game/panels/PhenomenonSelectorModal.vue'
import AvatarOverviewModal from '@/components/game/panels/AvatarOverviewModal.vue'

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
  <RankingModal v-model:show="showRankingModal" />
  <TimeOverviewModal v-model:show="showTimeOverviewModal" />
  <WorldInfoModal v-model:show="showWorldInfoModal" />
  <TournamentModal v-model:show="showTournamentModal" />
  <SectRelationsModal v-model:show="showSectRelationsModal" />
  <HiddenDomainOverviewModal v-model:show="showHiddenDomainModal" />
  <MortalOverviewModal v-model:show="showMortalOverviewModal" />
  <DynastyOverviewModal v-model:show="showDynastyOverviewModal" />
  <PhenomenonSelectorModal v-model:show="showPhenomenonSelector" />
  <AvatarOverviewModal v-model:show="showAvatarOverviewModal" />
</template>
