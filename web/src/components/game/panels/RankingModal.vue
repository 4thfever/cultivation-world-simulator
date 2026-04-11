<script setup lang="ts">
import { ref, watch } from 'vue'
import { NModal, NTabs, NTabPane, NTable, NSpin } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { worldApi } from '../../../api/modules/world'
import type { RankingsDTO } from '@/types/api'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useUiStore } from '../../../stores/ui'
import { formatRealmStage } from '@/utils/cultivationText'
import { logError } from '@/utils/appError'
import trophyIcon from '@/assets/icons/ui/lucide/trophy.svg'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()
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

const openAvatarInfo = (id: string) => {
  uiStore.select('avatar', id)
  handleShowChange(false)
}

const openSectInfo = (id: string) => {
  uiStore.select('sect', id)
  handleShowChange(false)
}

const loading = ref(false)
const rankings = ref<RankingsDTO>({
  heaven: [],
  earth: [],
  human: [],
  sect: []
})

const fetchRankings = async () => {
  loading.value = true
  try {
    const res = await worldApi.fetchRankings()
    rankings.value = res
  } catch (e) {
    logError('RankingModal fetch rankings', e)
  } finally {
    loading.value = false
  }
}

const handleShowChange = (val: boolean) => {
  emit('update:show', val)
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    fetchRankings()
  }
})
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.ranking.title')"
    style="width: 750px; max-height: 80vh; overflow-y: auto;"
  >
    <n-spin :show="loading">
      <div class="ranking-modal" :style="panelStyleVars">
        <div class="ranking-lead">
          <span class="lead-icon" :style="{ '--icon-url': `url(${trophyIcon})` }" aria-hidden="true"></span>
          <span>{{ t('game.ranking.title') }}</span>
        </div>
        <div style="display: flex; gap: 20px;">
        <div style="flex: 1; min-width: 0;">
          <n-tabs type="line" animated>
        <n-tab-pane name="heaven" :tab="t('game.ranking.heaven')">
          <n-table :bordered="false" :single-line="false" size="small">
            <thead>
              <tr>
                <th>{{ t('game.ranking.rank') }}</th>
                <th>{{ t('game.ranking.name') }}</th>
                <th>{{ t('game.ranking.sect') }}</th>
                <th>{{ t('game.ranking.realm') }}</th>
                <th>{{ t('game.ranking.power') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in rankings.heaven" :key="item.id">
                <td>{{ index + 1 }}</td>
                <td><a class="clickable-text" @click="openAvatarInfo(item.id)">{{ item.name }}</a></td>
                <td>
                  <a class="clickable-text" v-if="item.sect_id" @click="openSectInfo(item.sect_id)">{{ item.sect }}</a>
                  <span v-else>{{ item.sect }}</span>
                </td>
                <td>{{ formatRealmStage(item.realm, item.stage, t) }}</td>
                <td>{{ item.power }}</td>
              </tr>
              <tr v-if="!rankings.heaven.length">
                <td colspan="5" class="empty-cell">{{ t('game.ranking.empty') }}</td>
              </tr>
            </tbody>
          </n-table>
        </n-tab-pane>

        <n-tab-pane name="earth" :tab="t('game.ranking.earth')">
          <n-table :bordered="false" :single-line="false" size="small">
            <thead>
              <tr>
                <th>{{ t('game.ranking.rank') }}</th>
                <th>{{ t('game.ranking.name') }}</th>
                <th>{{ t('game.ranking.sect') }}</th>
                <th>{{ t('game.ranking.realm') }}</th>
                <th>{{ t('game.ranking.power') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in rankings.earth" :key="item.id">
                <td>{{ index + 1 }}</td>
                <td><a class="clickable-text" @click="openAvatarInfo(item.id)">{{ item.name }}</a></td>
                <td>
                  <a class="clickable-text" v-if="item.sect_id" @click="openSectInfo(item.sect_id)">{{ item.sect }}</a>
                  <span v-else>{{ item.sect }}</span>
                </td>
                <td>{{ formatRealmStage(item.realm, item.stage, t) }}</td>
                <td>{{ item.power }}</td>
              </tr>
              <tr v-if="!rankings.earth.length">
                <td colspan="5" class="empty-cell">{{ t('game.ranking.empty') }}</td>
              </tr>
            </tbody>
          </n-table>
        </n-tab-pane>

        <n-tab-pane name="human" :tab="t('game.ranking.human')">
          <n-table :bordered="false" :single-line="false" size="small">
            <thead>
              <tr>
                <th>{{ t('game.ranking.rank') }}</th>
                <th>{{ t('game.ranking.name') }}</th>
                <th>{{ t('game.ranking.sect') }}</th>
                <th>{{ t('game.ranking.realm') }}</th>
                <th>{{ t('game.ranking.power') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in rankings.human" :key="item.id">
                <td>{{ index + 1 }}</td>
                <td><a class="clickable-text" @click="openAvatarInfo(item.id)">{{ item.name }}</a></td>
                <td>
                  <a class="clickable-text" v-if="item.sect_id" @click="openSectInfo(item.sect_id)">{{ item.sect }}</a>
                  <span v-else>{{ item.sect }}</span>
                </td>
                <td>{{ formatRealmStage(item.realm, item.stage, t) }}</td>
                <td>{{ item.power }}</td>
              </tr>
              <tr v-if="!rankings.human.length">
                <td colspan="5" class="empty-cell">{{ t('game.ranking.empty') }}</td>
              </tr>
            </tbody>
          </n-table>
        </n-tab-pane>

        <n-tab-pane name="sect" :tab="t('game.ranking.sect_ranking')">
          <n-table :bordered="false" :single-line="false" size="small">
            <thead>
              <tr>
                <th>{{ t('game.ranking.rank') }}</th>
                <th>{{ t('game.ranking.sect_name') }}</th>
                <th>{{ t('game.ranking.alignment') }}</th>
                <th>{{ t('game.ranking.member_count') }}</th>
                <th>{{ t('game.ranking.total_power') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in rankings.sect" :key="item.id">
                <td>{{ index + 1 }}</td>
                <td><a class="clickable-text" @click="openSectInfo(item.id)">{{ item.name }}</a></td>
                <td>{{ item.alignment }}</td>
                <td>{{ item.member_count }}</td>
                <td>{{ item.total_power }}</td>
              </tr>
              <tr v-if="!rankings.sect.length">
                <td colspan="5" class="empty-cell">{{ t('game.ranking.empty') }}</td>
              </tr>
            </tbody>
          </n-table>
        </n-tab-pane>
      </n-tabs>
        </div>
      </div>
      </div>
    </n-spin>
  </n-modal>
</template>

<style scoped>
.clickable-text {
  color: var(--panel-link);
  cursor: pointer;
  text-decoration: none;
  transition: color 0.2s;
}

.clickable-text:hover {
  color: var(--panel-link-hover);
  text-decoration: underline;
}

:deep(.n-tabs-tab) {
  color: var(--panel-text-secondary);
}

:deep(.n-tabs-tab.n-tabs-tab--active) {
  color: var(--panel-accent-strong);
}

:deep(.n-tabs-bar) {
  background-color: var(--panel-accent-soft);
}

:deep(.n-table) {
  background-color: transparent;
}
:deep(.n-table th) {
  font-weight: bold;
  color: var(--panel-text-secondary);
}

.ranking-lead {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: var(--panel-title);
  font-weight: 700;
}

.lead-icon {
  width: 1em;
  height: 1em;
  display: inline-block;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
}

.empty-cell {
  text-align: center;
  color: var(--panel-empty);
}
</style>
