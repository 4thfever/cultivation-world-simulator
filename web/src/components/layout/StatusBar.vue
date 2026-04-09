<script setup lang="ts">
import { useWorldStore } from '../../stores/world'
import { useSocketStore } from '../../stores/socket'
import { ref, computed } from 'vue'
import { NModal, NList, NListItem, NTag, NEmpty, useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import StatusWidget from './StatusWidget.vue'
import { useWorldInfo } from '../../composables/useWorldInfo'

import RankingModal from '../game/panels/RankingModal.vue'
import TournamentModal from '../game/panels/TournamentModal.vue'
import SectRelationsModal from '../game/panels/SectRelationsModal.vue'
import MortalOverviewModal from '../game/panels/MortalOverviewModal.vue'
import DynastyOverviewModal from '../game/panels/DynastyOverviewModal.vue'
import bookOpenIcon from '@/assets/icons/ui/lucide/book-open.svg'
import sparklesIcon from '@/assets/icons/ui/lucide/sparkles.svg'
import shieldIcon from '@/assets/icons/ui/lucide/shield.svg'
import trophyIcon from '@/assets/icons/ui/lucide/trophy.svg'
import swordsIcon from '@/assets/icons/ui/lucide/swords.svg'
import usersIcon from '@/assets/icons/ui/lucide/users.svg'
import landmarkIcon from '@/assets/icons/ui/lucide/landmark.svg'

const { t, locale } = useI18n()
const store = useWorldStore()
const socketStore = useSocketStore()
const { entries: worldInfoEntries, loading: worldInfoLoading } = useWorldInfo()
const message = useMessage()
const showSelector = ref(false)
const showWorldInfoModal = ref(false)
const showRankingModal = ref(false)
const showTournamentModal = ref(false)
const showSectRelationsModal = ref(false)
const showMortalOverviewModal = ref(false)
const showDynastyOverviewModal = ref(false)

const phenomenonColor = computed(() => {
  const p = store.currentPhenomenon;
  if (!p) return '#ccc';
  return getRarityColor(p.rarity);
})

const domainLabel = computed(() => {
  return t('game.status_bar.hidden_domain.label');
});

const domainColor = computed(() => {
  // 如果有任意一个秘境是开启状态，则亮色
  const anyOpen = store.activeDomains.some(d => d.is_open);
  return anyOpen ? '#fa8c16' : '#666'; // 有开启亮橙色，全关闭灰色
});

const timeLabel = computed(() => {
  const yearPart = `${store.year}${t('common.year')}`;
  const monthPart = `${store.month}${t('common.month')}`;
  if (locale.value.startsWith('ja') || locale.value.startsWith('zh')) {
    return `${yearPart}${monthPart}`;
  }
  return `${yearPart} ${monthPart}`;
});

function getRarityColor(rarity: string) {
  switch (rarity) {
    case 'N': return '#ccc';
    case 'R': return '#4dabf7'; // Blue
    case 'SR': return '#a0d911'; // Lime
    case 'SSR': return '#fa8c16'; // Orange/Gold
    default: return '#ccc';
  }
}
async function openPhenomenonSelector() {
  await store.getPhenomenaList()
  showSelector.value = true
}

async function handleSelect(id: number, name: string) {
  try {
    await store.changePhenomenon(id)
    message.success(t('game.status_bar.change_success', { name }))
    showSelector.value = false
  } catch (e) {
    message.error(t('common.error'))
  }
}
</script>

<template>
  <header class="top-bar">
    <div class="left">
      <span class="title">{{ t('splash.title') }}</span>
      <span class="status-dot" :class="{ connected: socketStore.isConnected }"></span>
    </div>
    <div class="center">
      <span class="time">{{ timeLabel }}</span>

      <StatusWidget
        :label="t('game.status_bar.world_info.label')"
        :icon="bookOpenIcon"
        color="#91caff"
        mode="single"
        :disable-popover="true"
        @trigger-click="showWorldInfoModal = true"
      >
      </StatusWidget>
      
      <!-- 天地灵机 -->
      <StatusWidget 
        v-if="store.currentPhenomenon"
        :label="`[${store.currentPhenomenon.name}]`"
        :icon="sparklesIcon"
        :color="phenomenonColor"
        mode="single"
        :disable-popover="true"
        @trigger-click="openPhenomenonSelector"
      />

      <!-- 秘境 -->
      <StatusWidget
        :label="domainLabel"
        :icon="shieldIcon"
        :color="domainColor"
        mode="list"
        :title="t('game.status_bar.hidden_domain.title')"
        :items="store.activeDomains"
        :empty-text="t('game.status_bar.hidden_domain.empty')"
      />

      <!-- 榜单 -->
      <StatusWidget
        :label="t('game.ranking.title_short')"
        :icon="trophyIcon"
        color="#d4b106"
        mode="single"
        :disable-popover="true"
        @trigger-click="showRankingModal = true"
      />

      <!-- 武道会 -->
      <StatusWidget
        :label="t('game.ranking.tournament_short')"
        :icon="swordsIcon"
        color="#d4b106"
        mode="single"
        :disable-popover="true"
        @trigger-click="showTournamentModal = true"
      />

      <!-- 宗门关系 -->
      <StatusWidget
        :label="t('game.sect_relations.title_short')"
        :icon="shieldIcon"
        color="#597ef7"
        mode="single"
        :disable-popover="true"
        @trigger-click="showSectRelationsModal = true"
      />

      <StatusWidget
        :label="t('game.mortal_system.title_short')"
        :icon="usersIcon"
        color="#73d13d"
        mode="single"
        :disable-popover="true"
        @trigger-click="showMortalOverviewModal = true"
      />

      <StatusWidget
        :label="t('game.dynasty.title_short')"
        :icon="landmarkIcon"
        color="#d46b08"
        mode="single"
        :disable-popover="true"
        @trigger-click="showDynastyOverviewModal = true"
      />
    </div>

    <!-- 榜单 Modal -->
    <RankingModal v-model:show="showRankingModal" />

    <n-modal
      v-model:show="showWorldInfoModal"
      preset="card"
      :title="t('game.status_bar.world_info.title')"
      style="width: 820px; max-height: 80vh; overflow-y: auto;"
    >
      <div class="world-info-card">
        <div class="world-info-note">{{ t('game.status_bar.world_info.ai_knowledge_note') }}</div>

        <div v-if="worldInfoEntries.length > 0" class="world-info-list">
          <div
            v-for="entry in worldInfoEntries"
            :key="entry.id"
            class="world-info-item"
          >
            <div class="world-info-item-title">{{ entry.title }}</div>
            <div class="world-info-item-desc">{{ entry.desc }}</div>
          </div>
        </div>

        <div v-else class="world-info-empty">
          {{ worldInfoLoading ? t('common.loading') : t('game.status_bar.world_info.empty') }}
        </div>
      </div>
    </n-modal>
    
    <!-- 武道会 Modal -->
    <TournamentModal v-model:show="showTournamentModal" />

    <!-- 宗门关系 Modal -->
    <SectRelationsModal v-model:show="showSectRelationsModal" />

    <!-- 凡人系统 Modal -->
    <MortalOverviewModal v-model:show="showMortalOverviewModal" />

    <!-- 王朝系统 Modal -->
    <DynastyOverviewModal v-model:show="showDynastyOverviewModal" />

    <!-- 天象选择器 Modal -->
    <n-modal
      v-model:show="showSelector"
      preset="card"
      :title="t('game.status_bar.selector_title')"
      style="width: 700px; max-height: 80vh; overflow-y: auto;"
    >
      <n-list hoverable clickable>
        <n-list-item v-for="p in store.phenomenaList" :key="p.id" @click="handleSelect(p.id, p.name)" v-sound:select>
          <div class="list-item-content">
            <div class="item-left">
              <div class="item-name" :style="{ color: getRarityColor(p.rarity) }">
                {{ p.name }}
                <n-tag size="small" :bordered="false" :color="{ color: 'rgba(255,255,255,0.1)', textColor: getRarityColor(p.rarity) }">
                  {{ p.rarity }}
                </n-tag>
              </div>
              <div class="item-desc">{{ p.desc }}</div>
            </div>
            <div class="item-right">
               <div class="item-effect" v-if="p.effect_desc">{{ p.effect_desc }}</div>
            </div>
          </div>
        </n-list-item>
        <n-empty v-if="store.phenomenaList.length === 0" :description="t('game.status_bar.empty_data')" />
      </n-list>
    </n-modal>

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
  background: #1f1f1f;
  border-bottom: 1px solid #333;
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
}

.center {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* .phenomenon, .divider, .phenomenon-name REMOVED (moved to StatusWidget) */

.phenomenon-card {
  padding: 4px 0;
}

.p-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: bold;
  font-size: 15px;
  border-bottom: 1px solid #333;
  padding-bottom: 4px;
}

.p-rarity {
  font-size: 12px;
  opacity: 0.8;
  border: 1px solid currentColor;
  padding: 0 4px;
  border-radius: 2px;
}

.p-desc {
  font-size: 13px;
  color: #ddd;
  line-height: 1.5;
  margin-bottom: 8px;
}

/* 统一的效果块样式 */
.effect-block {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid #444;
  border-radius: 4px;
  padding: 8px 10px;
  margin: 8px 0;
}

.world-info-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.world-info-note {
  font-size: 12px;
  line-height: 1.5;
  color: #999;
  padding: 0 0 10px;
  border-bottom: 1px solid #2f2f2f;
}

.world-info-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.world-info-item {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  column-gap: 12px;
  align-items: start;
  padding: 8px 0;
  border-bottom: 1px solid #2f2f2f;
}

.world-info-item-title {
  font-size: 13px;
  font-weight: bold;
  color: #ddd;
  line-height: 1.6;
  white-space: nowrap;
}

.world-info-item-desc {
  font-size: 12px;
  line-height: 1.6;
  color: #bfbfbf;
  min-width: 0;
}

.world-info-empty {
  font-size: 12px;
  color: #8c8c8c;
  padding: 8px 0;
}

@media (max-width: 640px) {
  .world-info-item {
    grid-template-columns: 1fr;
    row-gap: 2px;
  }

  .world-info-item-title {
    white-space: normal;
  }
}

.effect-label {
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
}

.effect-content {
  font-size: 13px;
  color: #fadb14; /* 亮黄色，匹配游戏常见的高亮色 */
  font-weight: 500;
  line-height: 1.5;
  white-space: pre-wrap;
}

.p-duration {
  font-size: 12px;
  color: #888;
  text-align: right;
}

.click-tip {
  font-size: 10px;
  color: #666;
  text-align: center;
  margin-top: 8px;
  border-top: 1px dashed #333;
  padding-top: 4px;
}

.list-item-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 0;
}

.item-name {
  font-weight: bold;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-desc {
  color: #aaa;
  font-size: 13px;
}

.item-effect {
  font-size: 12px;
  color: #e6a23c; /* Warning color */
  background: rgba(230, 162, 60, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 4px;
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
