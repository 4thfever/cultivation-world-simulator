<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { useWorldStore } from '../../stores/world'
import { NSelect } from 'naive-ui'

const worldStore = useWorldStore()
const filterValue = ref('all')
const eventListRef = ref<HTMLElement | null>(null)

const filterOptions = computed(() => [
  { label: '所有人', value: 'all' },
  ...worldStore.avatarList.map(avatar => ({ 
    label: (avatar.name ?? avatar.id) + (avatar.is_dead ? ' (已故)' : ''), 
    value: avatar.id 
  }))
])

const filteredEvents = computed(() => {
  const allEvents = worldStore.events || []
  if (filterValue.value === 'all') {
    return allEvents
  }
  return allEvents.filter(event => event.relatedAvatarIds.includes(filterValue.value))
})

// 智能滚动：仅当用户处于底部时才自动跟随滚动
watch(filteredEvents, () => {
  const el = eventListRef.value
  let shouldAutoScroll = false

  if (!el) {
    // 之前没有元素（列表为空），现在有新数据进入，应当默认滚动到底部
    shouldAutoScroll = true
  } else {
    // 元素存在，判断当前是否处于底部
    // 1. 如果内容不满一页，视为“在底部”
    // 2. 如果已溢出，判断距离底部的位置（阈值 50px）
    const isScrollable = el.scrollHeight > el.clientHeight
    const isAtBottom = !isScrollable || (el.scrollHeight - el.scrollTop - el.clientHeight < 50)
    shouldAutoScroll = isAtBottom
  }

  if (shouldAutoScroll) {
    nextTick(() => {
      // DOM更新后再次获取元素
      const updatedEl = eventListRef.value
      if (updatedEl) {
        updatedEl.scrollTop = updatedEl.scrollHeight
      }
    })
  }
}, { deep: true })

// 切换筛选对象时，强制滚动到底部
watch(filterValue, () => {
  nextTick(() => {
    if (eventListRef.value) {
      eventListRef.value.scrollTop = eventListRef.value.scrollHeight
    }
  })
})

const emptyEventMessage = computed(() => (
  filterValue.value === 'all' ? '暂无事件' : '该修士暂无事件'
))

function formatEventDate(event: { year: number; month: number }) {
  return `${event.year}年${event.month}月`
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
    <div v-else class="event-list" ref="eventListRef">
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
