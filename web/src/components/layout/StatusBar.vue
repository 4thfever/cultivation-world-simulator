<script setup lang="ts">
import { useWorldStore } from '../../stores/world'
import { useSocketStore } from '../../stores/socket'
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import StatusWidget from './StatusWidget.vue'

import RankingModal from '../game/panels/RankingModal.vue'
import TournamentModal from '../game/panels/TournamentModal.vue'
import SectRelationsModal from '../game/panels/SectRelationsModal.vue'
import MortalOverviewModal from '../game/panels/MortalOverviewModal.vue'
import DynastyOverviewModal from '../game/panels/DynastyOverviewModal.vue'
import HiddenDomainOverviewModal from '../game/panels/HiddenDomainOverviewModal.vue'
import WorldInfoModal from '../game/panels/WorldInfoModal.vue'
import TimeOverviewModal from '../game/panels/TimeOverviewModal.vue'
import PhenomenonSelectorModal from '../game/panels/PhenomenonSelectorModal.vue'
import AvatarOverviewModal from '../game/panels/AvatarOverviewModal.vue'
import { PHENOMENON_RARITY_COLORS, STATUS_BAR_COLORS } from '@/constants/uiColors'
import { useAvatarOverviewStore } from '@/stores/avatarOverview'
import calendarIcon from '@/assets/icons/ui/lucide/calendar.svg'
import bookOpenIcon from '@/assets/icons/ui/lucide/book-open.svg'
import sparklesIcon from '@/assets/icons/ui/lucide/sparkles.svg'
import shieldIcon from '@/assets/icons/ui/lucide/shield.svg'
import trophyIcon from '@/assets/icons/ui/lucide/trophy.svg'
import swordsIcon from '@/assets/icons/ui/lucide/swords.svg'
import usersIcon from '@/assets/icons/ui/lucide/users.svg'
import landmarkIcon from '@/assets/icons/ui/lucide/landmark.svg'
import clock3Icon from '@/assets/icons/ui/lucide/clock-3.svg'

const { t, locale } = useI18n()
const store = useWorldStore()
const socketStore = useSocketStore()
const avatarOverviewStore = useAvatarOverviewStore()
const showSelector = ref(false)
const showTimeOverviewModal = ref(false)
const showWorldInfoModal = ref(false)
const showRankingModal = ref(false)
const showTournamentModal = ref(false)
const showSectRelationsModal = ref(false)
const showMortalOverviewModal = ref(false)
const showDynastyOverviewModal = ref(false)
const showHiddenDomainModal = ref(false)
const showAvatarOverviewModal = ref(false)

const phenomenonColor = computed(() => {
  const p = store.currentPhenomenon
  if (!p) return STATUS_BAR_COLORS.neutral
  return getRarityColor(p.rarity)
})

const domainLabel = computed(() => {
  return t('game.status_bar.hidden_domain.label')
})

const avatarOverviewLabel = computed(() => {
  return t('game.status_bar.avatar_overview.label')
})

const timeLabel = computed(() => {
  const yearPart = `${store.year}${t('common.year')}`
  const monthPart = `${store.month}${t('common.month')}`
  if (locale.value.startsWith('ja') || locale.value.startsWith('zh')) {
    return `${yearPart}${monthPart}`
  }
  return `${yearPart} ${monthPart}`
})

function getRarityColor(rarity: string) {
  return PHENOMENON_RARITY_COLORS[rarity] ?? STATUS_BAR_COLORS.neutral
}
async function openPhenomenonSelector() {
  await store.getPhenomenaList()
  showSelector.value = true
}

async function openAvatarOverview() {
  if (!avatarOverviewStore.isLoaded) {
    await avatarOverviewStore.refreshOverview()
  }
  showAvatarOverviewModal.value = true
}
</script>

<template>
  <header class="top-bar">
    <div class="left">
      <span class="title">{{ t('splash.title') }}</span>
      <span class="status-dot" :class="{ connected: socketStore.isConnected }"></span>
    </div>
    <div class="center">
      <StatusWidget
        :label="timeLabel"
        :icon="calendarIcon"
        :color="STATUS_BAR_COLORS.time"
        :disable-popover="true"
        @trigger-click="showTimeOverviewModal = true"
      />

      <StatusWidget
        v-if="store.currentPhenomenon"
        :label="`[${store.currentPhenomenon.name}]`"
        :icon="sparklesIcon"
        :color="phenomenonColor"
        :disable-popover="true"
        @trigger-click="openPhenomenonSelector"
      />

      <StatusWidget
        :label="domainLabel"
        :icon="shieldIcon"
        :color="STATUS_BAR_COLORS.hiddenDomain"
        :disable-popover="true"
        @trigger-click="showHiddenDomainModal = true"
      />

      <StatusWidget
        :label="t('game.sect_relations.title_short')"
        :icon="shieldIcon"
        :color="STATUS_BAR_COLORS.sectRelations"
        :disable-popover="true"
        @trigger-click="showSectRelationsModal = true"
      />

      <StatusWidget
        :label="t('game.dynasty.title_short')"
        :icon="landmarkIcon"
        :color="STATUS_BAR_COLORS.dynasty"
        :disable-popover="true"
        @trigger-click="showDynastyOverviewModal = true"
      />

      <StatusWidget
        :label="t('game.mortal_system.title_short')"
        :icon="usersIcon"
        :color="STATUS_BAR_COLORS.mortal"
        :disable-popover="true"
        @trigger-click="showMortalOverviewModal = true"
      />

      <StatusWidget
        :label="t('game.ranking.title_short')"
        :icon="trophyIcon"
        :color="STATUS_BAR_COLORS.ranking"
        :disable-popover="true"
        @trigger-click="showRankingModal = true"
      />

      <StatusWidget
        :label="t('game.ranking.tournament_short')"
        :icon="swordsIcon"
        :color="STATUS_BAR_COLORS.tournament"
        :disable-popover="true"
        @trigger-click="showTournamentModal = true"
      />

      <StatusWidget
        :label="avatarOverviewLabel"
        :icon="clock3Icon"
        :color="STATUS_BAR_COLORS.neutral"
        :disable-popover="true"
        @trigger-click="openAvatarOverview"
      />

      <StatusWidget
        :label="t('game.status_bar.world_info.label')"
        :icon="bookOpenIcon"
        :color="STATUS_BAR_COLORS.worldInfo"
        :disable-popover="true"
        @trigger-click="showWorldInfoModal = true"
      />
    </div>

    <RankingModal v-model:show="showRankingModal" />
    <TimeOverviewModal v-model:show="showTimeOverviewModal" />
    <WorldInfoModal v-model:show="showWorldInfoModal" />
    
    <TournamentModal v-model:show="showTournamentModal" />

    <SectRelationsModal v-model:show="showSectRelationsModal" />

    <HiddenDomainOverviewModal v-model:show="showHiddenDomainModal" />

    <MortalOverviewModal v-model:show="showMortalOverviewModal" />

    <DynastyOverviewModal v-model:show="showDynastyOverviewModal" />
    <PhenomenonSelectorModal v-model:show="showSelector" />
    <AvatarOverviewModal v-model:show="showAvatarOverviewModal" />

    <div class="author">
      <a
        class="author-link"
        href="https://github.com/4thfever/cultivation-world-simulator"
        target="_blank"
        rel="noopener"
      >
        {{ t('game.status_bar.author_github') }}
      </a>
    </div>
  </header>
</template>

<style scoped>
.top-bar {
  height: 36px;
  background:
    linear-gradient(180deg, rgba(34, 34, 34, 0.98), rgba(22, 22, 22, 0.98)),
    linear-gradient(90deg, rgba(120, 182, 255, 0.08), rgba(227, 179, 65, 0.04) 38%, rgba(95, 191, 122, 0.06) 100%);
  border-bottom: 1px solid #2f2f2f;
  box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.03);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  font-size: 14px;
  z-index: 10;
  gap: 16px;
}

.top-bar .title {
  font-weight: bold;
  margin-right: 8px;
  color: #e8dcc0;
  letter-spacing: 0.04em;
}

.center {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ff4d4f;
}

.status-dot.connected {
  background: #52c41a;
}

.author {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  color: #bbb;
  display: none; /* 暂时隐藏，因为空间可能不够 */
}

@media (min-width: 1024px) {
  .author {
    display: flex;
  }
}

.author-link {
  color: #4dabf7;
  text-decoration: none;
}

.author-link:hover {
  color: #8bc6ff;
  text-decoration: underline;
}
</style>
