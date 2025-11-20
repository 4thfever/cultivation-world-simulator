<script setup lang="ts">
import { computed, ref } from 'vue'
import { useGameStore } from '../../stores/game'
import { NSelect } from 'naive-ui'

const store = useGameStore()
const filterValue = ref('all')

const filterOptions = computed(() => [
  { label: '所有人', value: 'all' },
  ...store.avatarList.map(avatar => ({ label: avatar.name ?? avatar.id, value: avatar.id }))
])

const filteredEvents = computed(() => {
  const allEvents = Array.isArray(store.events) ? store.events : []
  if (filterValue.value === 'all') {
    return allEvents
  }
  return allEvents.filter(event => event.relatedAvatarIds.includes(filterValue.value))
})

const emptyEventMessage = computed(() => (
  filterValue.value === 'all' ? '暂无事件' : '该修士暂无事件'
))

function formatEventDate(event: { year?: number; month?: number; monthStamp?: number }) {
  if (typeof event.year === 'number' && typeof event.month === 'number') {
    return `${event.year}年${event.month}月`
  }
  if (typeof event.monthStamp === 'number') {
    const year = Math.floor(event.monthStamp / 12)
    const month = event.monthStamp % 12 || 12
    return `${year}年${month}月`
  }
  return '未知'
}
</script>

<template>
  <section class="sidebar-section">
    <div class="sidebar-header">
      <h3>事件记录</h3>
      <n-select
        v-model:value="filterValue"
        :options="filterOptions"
        size="tiny"
        class="event-filter"
      />
    </div>
    <div v-if="filteredEvents.length === 0" class="empty">{{ emptyEventMessage }}</div>
    <div v-else class="event-list">
      <div v-for="event in filteredEvents" :key="event.id" class="event-item">
        <div class="event-date">{{ formatEventDate(event) }}</div>
        <div class="event-content">{{ event.content || event.text }}</div>
      </div>
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

.event-filter {
  width: 200px;
}

.event-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
}

.event-item {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #2a2a2a;
}

.event-item:last-child {
  border-bottom: none;
}

.event-date {
  flex: 0 0 25%;
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.event-content {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
  color: #ddd;
  white-space: pre-line;
}

.empty {
  padding: 20px;
  text-align: center;
  color: #666;
  font-size: 12px;
}
</style>

