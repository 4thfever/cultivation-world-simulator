<script setup lang="ts">
import { ref, watch } from 'vue'
import { NModal, NSpin, NEmpty } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { worldApi } from '../../../api/modules/world'
import type { RankingsDTO } from '@/types/api'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useWorldStore } from '../../../stores/world'
import { useUiStore } from '../../../stores/ui'
import { logError } from '@/utils/appError'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()
const uiStore = useUiStore()
const worldStore = useWorldStore()
const tournamentTheme = SYSTEM_PANEL_THEMES.tournament
const panelStyleVars = {
  '--panel-accent': tournamentTheme.accent,
  '--panel-accent-strong': tournamentTheme.accentStrong,
  '--panel-accent-soft': tournamentTheme.accentSoft,
  '--panel-link': tournamentTheme.link,
  '--panel-link-hover': tournamentTheme.linkHover,
  '--panel-title': tournamentTheme.title,
  '--panel-empty': tournamentTheme.empty,
  '--panel-border': tournamentTheme.border,
  '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
  '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
  '--panel-text-muted': SHARED_UI_COLORS.textMuted,
}

const openAvatarInfo = (id: string) => {
  uiStore.select('avatar', id)
  handleShowChange(false)
}

const loading = ref(false)
const rankings = ref<RankingsDTO>({
  heaven: [],
  earth: [],
  human: [],
  sect: [],
})

const fetchRankings = async () => {
  loading.value = true
  try {
    const res = await worldApi.fetchRankings()
    rankings.value = res
  } catch (e) {
    logError('TournamentModal fetch rankings', e)
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
    :title="t('game.ranking.tournament_title')"
    style="width: 400px; max-height: 80vh; overflow-y: auto;"
  >
    <n-spin :show="loading">
      <div class="tournament-panel" :style="panelStyleVars">
        <div v-if="rankings.tournament">
        <div class="next-time">
          {{ t('game.ranking.tournament_next', { years: Math.max(0, rankings.tournament.next_year - worldStore.year) }) }}
        </div>
        
        <div class="winner-list">
          <div class="winner-card">
            <div class="winner-label">{{ t('game.ranking.heaven_first') }}</div>
            <a v-if="rankings.tournament.heaven_first" class="clickable-text" @click="openAvatarInfo(rankings.tournament.heaven_first.id)">
              {{ rankings.tournament.heaven_first.name }}
            </a>
            <span v-else class="empty-inline">{{ t('game.ranking.empty') }}</span>
          </div>
          
          <div class="winner-card">
            <div class="winner-label">{{ t('game.ranking.earth_first') }}</div>
            <a v-if="rankings.tournament.earth_first" class="clickable-text" @click="openAvatarInfo(rankings.tournament.earth_first.id)">
              {{ rankings.tournament.earth_first.name }}
            </a>
            <span v-else class="empty-inline">{{ t('game.ranking.empty') }}</span>
          </div>
          
          <div class="winner-card">
            <div class="winner-label">{{ t('game.ranking.human_first') }}</div>
            <a v-if="rankings.tournament.human_first" class="clickable-text" @click="openAvatarInfo(rankings.tournament.human_first.id)">
              {{ rankings.tournament.human_first.name }}
            </a>
            <span v-else class="empty-inline">{{ t('game.ranking.empty') }}</span>
          </div>
        </div>
      </div>
      <n-empty v-else :description="t('game.ranking.empty')" class="empty-block" />
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
  font-weight: 700;
}

.clickable-text:hover {
  color: var(--panel-link-hover);
  text-decoration: underline;
}

.next-time {
  margin-bottom: 16px;
  color: var(--panel-title);
}

.winner-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.winner-card {
  padding: 12px;
  border: 1px solid var(--panel-border);
  border-radius: 6px;
  background: var(--panel-accent-soft);
}

.winner-label {
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--panel-text-primary);
}

.empty-inline {
  color: var(--panel-empty);
}

.empty-block {
  margin: 20px 0;
}
</style>
