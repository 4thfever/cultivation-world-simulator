<script setup lang="ts">
import { NSelect, NSpin } from 'naive-ui'
import EventStreamList from '@/components/game/EventStreamList.vue'
import { useI18n } from 'vue-i18n'
import { useEventPanel } from '@/composables/useEventPanel'

const { t } = useI18n()
const {
  eventStore,
  filterValue1,
  filterSectValue,
  filterMajorScope,
  eventListRef,
  roleplayLockedAvatarName,
  filterOptions,
  sectFilterOptions,
  majorFilterOptions,
  panelTitle,
  displayEvents,
  emptyEventMessage,
  renderLabel,
  handleScroll,
  formatEventDate,
  renderEventContent,
  handleAvatarClick,
  handleSectClick,
} = useEventPanel()
</script>

<template>
  <section class="sidebar-section">
    <div class="sidebar-header">
      <h3>{{ panelTitle }}</h3>
      <div class="filter-group">
        <span v-if="roleplayLockedAvatarName" class="roleplay-event-lock">
          {{ t('game.event_panel.roleplay_locked', { avatar: roleplayLockedAvatarName }) }}
        </span>
        <n-select
          v-model:value="filterSectValue"
          :options="sectFilterOptions"
          size="tiny"
          class="event-filter"
          data-testid="sect-filter"
        />
        <n-select
          v-model:value="filterValue1"
          :options="filterOptions"
          :render-label="renderLabel"
          size="tiny"
          class="event-filter"
        />
        <n-select
          v-model:value="filterMajorScope"
          :options="majorFilterOptions"
          size="tiny"
          class="event-filter event-filter--scope"
          data-testid="major-filter"
        />
      </div>
    </div>
    <div v-if="eventStore.eventsLoading && displayEvents.length === 0" class="loading">
      <n-spin size="small" />
      <span>{{ t('common.loading') }}</span>
    </div>
    <div v-else-if="displayEvents.length === 0" class="empty">{{ emptyEventMessage }}</div>
    <div v-else class="event-list" ref="eventListRef" @scroll="handleScroll">
      <!-- 顶部加载指示器 -->
      <div v-if="eventStore.eventsHasMore" class="load-more-hint">
        <span v-if="eventStore.eventsLoading">{{ t('common.loading') }}</span>
        <span v-else>{{ t('game.event_panel.load_more') }}</span>
      </div>
      <EventStreamList
        :events="displayEvents"
        :empty-text="emptyEventMessage"
        :format-date="formatEventDate"
        :render-segments="renderEventContent"
        :on-avatar-click="handleAvatarClick"
        :on-sect-click="handleSectClick"
      />
    </div>
  </section>
</template>

<style scoped>
.sidebar-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #222;
  border-bottom: 1px solid #333;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 13px;
  white-space: nowrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.roleplay-event-lock {
  max-width: 160px;
  padding: 2px 7px;
  border-radius: 999px;
  border: 1px solid rgba(208, 180, 124, 0.24);
  color: #dec48b;
  background: rgba(86, 61, 23, 0.32);
  font-size: 11px;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-filter {
  width: 120px;
}

.event-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
}

.empty, .loading {
  padding: 20px;
  text-align: center;
  color: #666;
  font-size: 12px;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.load-more-hint {
  text-align: center;
  padding: 8px;
  color: #666;
  font-size: 11px;
  border-bottom: 1px solid #2a2a2a;
}
</style>
