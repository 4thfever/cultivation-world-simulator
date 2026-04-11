<script setup lang="ts">
import { ref, shallowRef, watch } from 'vue'
import { NModal, NTable, NSpin, NEmpty, NButton } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { worldApi } from '../../../api/modules/world'
import { eventApi } from '../../../api/modules/event'
import { mapDeceasedList } from '../../../api/mappers/deceased'
import type { DeceasedRecordView } from '../../../api/mappers/deceased'
import type { EventDTO } from '@/types/api'
import { formatRealmStage } from '@/utils/cultivationText'
import { logError } from '@/utils/appError'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()

const loading = ref(false)
const records = shallowRef<DeceasedRecordView[]>([])
const selectedRecord = ref<DeceasedRecordView | null>(null)
const eventsLoading = ref(false)
const events = shallowRef<EventDTO[]>([])

const fetchDeceased = async () => {
  loading.value = true
  try {
    const dtos = await worldApi.fetchDeceasedList()
    records.value = mapDeceasedList(dtos)
  } catch (e) {
    logError('DeceasedModal fetch deceased', e)
  } finally {
    loading.value = false
  }
}

const fetchEvents = async (avatarId: string) => {
  eventsLoading.value = true
  try {
    const res = await eventApi.fetchEvents({ avatar_id: avatarId, limit: 50 })
    events.value = res.events
  } catch (e) {
    logError('DeceasedModal fetch events', e)
  } finally {
    eventsLoading.value = false
  }
}

const selectRecord = (record: DeceasedRecordView) => {
  selectedRecord.value = record
  events.value = []
  fetchEvents(record.id)
}

const backToList = () => {
  selectedRecord.value = null
  events.value = []
}

const handleShowChange = (val: boolean) => {
  emit('update:show', val)
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    selectedRecord.value = null
    events.value = []
    fetchDeceased()
  }
})
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.deceased.title')"
    style="width: 700px; max-height: 80vh; overflow-y: auto;"
  >
    <!-- 详情视图 -->
    <template v-if="selectedRecord">
      <div style="margin-bottom: 12px;">
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

      <h4 style="margin: 16px 0 8px;">{{ t('game.deceased.events') }}</h4>
      <n-spin :show="eventsLoading">
        <div v-if="events.length === 0 && !eventsLoading" style="text-align: center; color: #888; padding: 16px;">
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

    <!-- 列表视图 -->
    <template v-else>
      <n-spin :show="loading">
        <n-empty v-if="!loading && records.length === 0" :description="t('game.deceased.empty')" />
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
  </n-modal>
</template>

<style scoped>
.clickable-row {
  cursor: pointer;
  transition: background-color 0.15s;
}
.clickable-row:hover {
  background-color: rgba(255, 255, 255, 0.06);
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
  color: #888;
  min-width: 80px;
  flex-shrink: 0;
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
  color: #888;
  margin-right: 6px;
}
.event-text {
  color: #ccc;
}

:deep(.n-table) {
  background-color: transparent;
}
:deep(.n-table th) {
  font-weight: bold;
}
</style>
