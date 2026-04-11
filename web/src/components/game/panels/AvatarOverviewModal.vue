<script setup lang="ts">
import { computed, ref, shallowRef, watch } from 'vue'
import { NButton, NEmpty, NModal, NSpin, NTable, NTabPane, NTabs } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { worldApi } from '@/api/modules/world'
import { eventApi } from '@/api/modules/event'
import { mapDeceasedList } from '@/api/mappers/deceased'
import { useAvatarOverviewStore } from '@/stores/avatarOverview'
import { formatRealmStage } from '@/utils/cultivationText'
import type { EventDTO } from '@/types/api'
import type { DeceasedRecordView } from '@/api/mappers/deceased'
import { logError } from '@/utils/appError'
import usersIcon from '@/assets/icons/ui/lucide/users.svg'
import trophyIcon from '@/assets/icons/ui/lucide/trophy.svg'

const props = defineProps<{
  show: boolean;
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void;
}>()

const { t } = useI18n()
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
const deceasedLoading = ref(false)
const deceasedLoaded = ref(false)
const records = shallowRef<DeceasedRecordView[]>([])
const selectedRecord = ref<DeceasedRecordView | null>(null)
const eventsLoading = ref(false)
const events = shallowRef<EventDTO[]>([])

function handleShowChange(value: boolean) {
  emit('update:show', value)
}

async function fetchDeceased() {
  deceasedLoading.value = true
  try {
    const dtos = await worldApi.fetchDeceasedList()
    records.value = mapDeceasedList(dtos)
    deceasedLoaded.value = true
  } catch (error) {
    logError('AvatarOverviewModal fetch deceased', error)
    records.value = []
    deceasedLoaded.value = false
  } finally {
    deceasedLoading.value = false
  }
}

async function fetchEvents(avatarId: string) {
  eventsLoading.value = true
  try {
    const res = await eventApi.fetchEvents({ avatar_id: avatarId, limit: 50 })
    events.value = res.events
  } catch (error) {
    logError('AvatarOverviewModal fetch events', error)
    events.value = []
  } finally {
    eventsLoading.value = false
  }
}

function selectRecord(record: DeceasedRecordView) {
  selectedRecord.value = record
  events.value = []
  void fetchEvents(record.id)
}

function backToList() {
  selectedRecord.value = null
  events.value = []
}

async function handleTabUpdate(value: string) {
  activeTab.value = value === 'deceased' ? 'deceased' : 'overview'
  if (activeTab.value === 'deceased' && !deceasedLoaded.value) {
    await fetchDeceased()
  }
}

watch(
  () => props.show,
  (show) => {
    if (show) {
      activeTab.value = 'overview'
      selectedRecord.value = null
      events.value = []
      void avatarOverviewStore.refreshOverview()
      return
    }

    activeTab.value = 'overview'
    selectedRecord.value = null
    events.value = []
  },
  { immediate: true },
)
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.avatar_overview.title')"
    style="width: 980px; max-height: 80vh; overflow-y: auto;"
  >
    <n-spin :show="avatarOverviewStore.isLoading">
      <div class="avatar-overview" :style="panelStyleVars">
        <n-tabs
          type="line"
          animated
          :value="activeTab"
          @update:value="handleTabUpdate"
        >
          <n-tab-pane name="overview" :tab="t('game.avatar_overview.tabs.overview')">
            <div class="tab-content">
              <section class="section">
                <div class="section-title">
                  <span class="section-title-icon" :style="{ '--icon-url': `url(${usersIcon})` }" aria-hidden="true"></span>
                  {{ t('game.avatar_overview.summary.title') }}
                </div>
                <div class="summary-grid">
                  <div class="summary-card">
                    <div class="summary-label">{{ t('game.avatar_overview.summary.total_count') }}</div>
                    <div class="summary-value">{{ summary.totalCount }}</div>
                  </div>
                  <div class="summary-card">
                    <div class="summary-label">{{ t('game.avatar_overview.summary.alive_count') }}</div>
                    <div class="summary-value success">{{ summary.aliveCount }}</div>
                  </div>
                  <div class="summary-card">
                    <div class="summary-label">{{ t('game.avatar_overview.summary.dead_count') }}</div>
                    <div class="summary-value danger">{{ summary.deadCount }}</div>
                  </div>
                  <div class="summary-card">
                    <div class="summary-label">{{ t('game.avatar_overview.summary.sect_member_count') }}</div>
                    <div class="summary-value">{{ summary.sectMemberCount }}</div>
                  </div>
                  <div class="summary-card">
                    <div class="summary-label">{{ t('game.avatar_overview.summary.rogue_count') }}</div>
                    <div class="summary-value">{{ summary.rogueCount }}</div>
                  </div>
                </div>
              </section>

              <section class="section">
                <div class="section-title">
                  <span class="section-title-icon" :style="{ '--icon-url': `url(${trophyIcon})` }" aria-hidden="true"></span>
                  {{ t('game.avatar_overview.realm_distribution.title') }}
                </div>
                <n-table :bordered="false" :single-line="false" size="small">
                  <thead>
                    <tr>
                      <th>{{ t('game.avatar_overview.realm_distribution.realm') }}</th>
                      <th>{{ t('game.avatar_overview.realm_distribution.count') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in realmDistribution" :key="item.realm">
                      <td>{{ item.realm }}</td>
                      <td>{{ item.count }}</td>
                    </tr>
                    <tr v-if="!realmDistribution.length">
                      <td colspan="2" class="empty-cell">{{ t('game.avatar_overview.empty') }}</td>
                    </tr>
                  </tbody>
                </n-table>
              </section>
            </div>
          </n-tab-pane>

          <n-tab-pane name="deceased" :tab="t('game.avatar_overview.tabs.deceased')">
            <div class="tab-content">
              <template v-if="selectedRecord">
                <div class="deceased-toolbar">
                  <n-button size="small" @click="backToList">{{ t('game.deceased.back_to_list') }}</n-button>
                </div>

                <div class="deceased-detail-card">
                  <div class="detail-row">
                    <span class="detail-label">{{ t('game.deceased.age_at_death') }}</span>
                    <span>{{ selectedRecord.ageAtDeath }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">{{ t('game.deceased.realm_at_death') }}</span>
                    <span>{{ formatRealmStage(selectedRecord.realmDisplay, selectedRecord.stageDisplay, t) }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">{{ t('game.deceased.death_reason') }}</span>
                    <span>{{ selectedRecord.deathReason }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">{{ t('game.deceased.death_time') }}</span>
                    <span>{{ t('game.deceased.death_year', { year: selectedRecord.deathYear, month: selectedRecord.deathMonth }) }}</span>
                  </div>
                  <div class="detail-row" v-if="selectedRecord.sectName">
                    <span class="detail-label">{{ t('game.deceased.sect') }}</span>
                    <span>{{ selectedRecord.sectName }}</span>
                  </div>
                  <div class="detail-row" v-if="selectedRecord.alignment">
                    <span class="detail-label">{{ t('game.deceased.alignment') }}</span>
                    <span>{{ selectedRecord.alignment }}</span>
                  </div>
                  <div class="detail-row" v-if="selectedRecord.backstory">
                    <span class="detail-label">{{ t('game.deceased.backstory') }}</span>
                    <span>{{ selectedRecord.backstory }}</span>
                  </div>
                </div>

                <h4 class="subsection-title">{{ t('game.deceased.events') }}</h4>
                <n-spin :show="eventsLoading">
                  <div v-if="events.length === 0 && !eventsLoading" class="empty-events">
                    {{ t('game.deceased.no_events') }}
                  </div>
                  <div v-else class="event-list">
                    <div v-for="evt in events" :key="evt.id" class="event-item">
                      <span class="event-time">[{{ evt.year }}-{{ evt.month }}]</span>
                      <span class="event-text">{{ evt.content }}</span>
                    </div>
                  </div>
                </n-spin>
              </template>

              <template v-else>
                <n-spin :show="deceasedLoading">
                  <n-empty
                    v-if="!deceasedLoading && records.length === 0"
                    :description="t('game.deceased.empty')"
                  />
                  <n-table v-else :bordered="false" :single-line="false" size="small" striped>
                    <thead>
                      <tr>
                        <th>{{ t('game.deceased.name') }}</th>
                        <th>{{ t('game.deceased.sect') }}</th>
                        <th>{{ t('game.deceased.realm_at_death') }}</th>
                        <th>{{ t('game.deceased.age_at_death') }}</th>
                        <th>{{ t('game.deceased.death_reason') }}</th>
                        <th>{{ t('game.deceased.death_time') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="record in records"
                        :key="record.id"
                        class="clickable-row"
                        @click="selectRecord(record)"
                      >
                        <td>{{ record.name }}</td>
                        <td>{{ record.sectName || t('game.deceased.rogue') }}</td>
                        <td>{{ formatRealmStage(record.realmDisplay, record.stageDisplay, t) }}</td>
                        <td>{{ record.ageAtDeath }}</td>
                        <td>{{ record.deathReason }}</td>
                        <td>{{ t('game.deceased.death_year', { year: record.deathYear, month: record.deathMonth }) }}</td>
                      </tr>
                    </tbody>
                  </n-table>
                </n-spin>
              </template>
            </div>
          </n-tab-pane>
        </n-tabs>
      </div>
    </n-spin>
  </n-modal>
</template>

<style scoped>
.avatar-overview {
  display: flex;
  flex-direction: column;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-top: 8px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--panel-title);
  border-bottom: 1px solid var(--panel-border);
  padding-bottom: 6px;
}

.section-title-icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
  flex-shrink: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}

.summary-card {
  padding: 10px 12px;
  border: 1px solid var(--panel-border);
  border-radius: 6px;
  background: var(--panel-accent-soft);
}

.summary-label {
  font-size: 12px;
  color: var(--panel-text-secondary);
  margin-bottom: 6px;
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--panel-text-primary);
}

.summary-value.success {
  color: var(--panel-accent-strong);
}

.summary-value.danger {
  color: #e5a693;
}

:deep(.n-table th) {
  color: var(--panel-text-secondary);
}

:deep(.n-tabs-tab) {
  color: var(--panel-text-secondary);
}

:deep(.n-tabs-tab.n-tabs-tab--active) {
  color: var(--panel-title);
}

:deep(.n-tabs-bar) {
  background: transparent;
}

.empty-cell {
  text-align: center;
  color: var(--panel-empty);
}

.clickable-row {
  cursor: pointer;
  transition: background-color 0.15s;
}

.clickable-row:hover {
  background-color: rgba(255, 255, 255, 0.06);
}

.deceased-toolbar {
  margin-bottom: 12px;
}

.deceased-detail-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.04);
}

.detail-row {
  display: flex;
  gap: 12px;
}

.detail-label {
  color: var(--panel-text-secondary);
  min-width: 80px;
  flex-shrink: 0;
}

.subsection-title {
  margin: 16px 0 8px;
  color: var(--panel-title);
}

.empty-events {
  text-align: center;
  color: var(--panel-empty);
  padding: 16px;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 300px;
  overflow-y: auto;
}

.event-item {
  font-size: 13px;
  line-height: 1.5;
}

.event-time {
  color: var(--panel-text-secondary);
  margin-right: 6px;
}

.event-text {
  color: var(--panel-text-primary);
}
</style>
