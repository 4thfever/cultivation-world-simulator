<script setup lang="ts">
import { computed, ref, watch, nextTick, onMounted, h } from 'vue'
import { useWorldStore } from '../../../stores/world'
import { useUiStore } from '../../../stores/ui'
import { NSelect, NSpin, NButton } from 'naive-ui'
import type { SelectOption } from 'naive-ui'
import { highlightAvatarNames, buildAvatarColorMap, avatarIdToColor } from '../../../utils/eventHelper'
import type { GameEvent } from '../../../types/core'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const worldStore = useWorldStore()
const uiStore = useUiStore()
const filterValue1 = ref('all')
const filterValue2 = ref<string | null>(null)  // null 表示未启用双人筛选
const eventListRef = ref<HTMLElement | null>(null)

const filterOptions = computed(() => [
  { label: t('game.event_panel.filter_all'), value: 'all' },
  ...worldStore.avatarList.map(avatar => ({
    label: (avatar.name ?? avatar.id) + (avatar.is_dead ? ` ${t('game.event_panel.deceased')}` : ''),
    value: avatar.id
  }))
])

// 第二人的选项（排除第一人和"所有人"）
const filterOptions2 = computed(() =>
  worldStore.avatarList
    .filter(avatar => avatar.id !== filterValue1.value)
    .map(avatar => ({
      label: (avatar.name ?? avatar.id) + (avatar.is_dead ? ` ${t('game.event_panel.deceased')}` : ''),
      value: avatar.id
    }))
)

// 直接使用 store 中的事件（已由 API 过滤）
const displayEvents = computed(() => worldStore.events || [])

// 渲染带颜色圆点的选项标签
const renderLabel = (option: SelectOption) => {
  if (option.value === 'all') return option.label as string
  
  const color = avatarIdToColor(option.value as string)
  return h('div', { style: { display: 'flex', alignItems: 'center', gap: '6px' } }, [
    h('span', {
      style: {
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        backgroundColor: color,
        flexShrink: 0
      }
    }),
    option.label as string
  ])
}

// 向上滚动加载更多
function handleScroll(e: Event) {
  const el = e.target as HTMLElement
  if (!el) return

  // 当滚动到顶部附近时，加载更多
  if (el.scrollTop < 100 && worldStore.eventsHasMore && !worldStore.eventsLoading) {
    const oldScrollHeight = el.scrollHeight
    worldStore.loadMoreEvents().then(() => {
      // 保持滚动位置（在顶部加载了新内容后）
      nextTick(() => {
        const newScrollHeight = el.scrollHeight
        el.scrollTop = newScrollHeight - oldScrollHeight + el.scrollTop
      })
    })
  }
}

// 构建筛选参数
function buildFilter() {
  if (filterValue2.value && filterValue1.value !== 'all') {
    // 双人筛选
    return { avatar_id_1: filterValue1.value, avatar_id_2: filterValue2.value }
  } else if (filterValue1.value !== 'all') {
    // 单人筛选
    return { avatar_id: filterValue1.value }
  }
  return {}
}

// 加载事件并滚动到底部
async function reloadEvents() {
  await worldStore.resetEvents(buildFilter())
  nextTick(() => {
    if (eventListRef.value) {
      eventListRef.value.scrollTop = eventListRef.value.scrollHeight
    }
  })
}

// 切换第一人筛选
watch(filterValue1, async (newVal) => {
  // 如果选了"所有人"，清除第二人筛选
  if (newVal === 'all') {
    filterValue2.value = null
  }
  await reloadEvents()
})

// 切换第二人筛选
watch(filterValue2, async () => {
  await reloadEvents()
})

// 添加第二人
function addSecondFilter() {
  // 默认选择列表中的第一个（排除当前第一人）
  const options = filterOptions2.value
  if (options.length > 0) {
    filterValue2.value = options[0].value
  }
}

// 移除第二人筛选
function removeSecondFilter() {
  filterValue2.value = null
}

// 智能滚动：仅当用户处于底部时才自动跟随滚动（用于实时推送的新事件）
watch(displayEvents, () => {
  const el = eventListRef.value
  if (!el) return

  const isScrollable = el.scrollHeight > el.clientHeight
  const isAtBottom = !isScrollable || (el.scrollHeight - el.scrollTop - el.clientHeight < 50)

  if (isAtBottom) {
    nextTick(() => {
      if (eventListRef.value) {
        eventListRef.value.scrollTop = eventListRef.value.scrollHeight
      }
    })
  }
}, { deep: true })

// 初始加载
onMounted(async () => {
  await worldStore.resetEvents({})
  nextTick(() => {
    if (eventListRef.value) {
      eventListRef.value.scrollTop = eventListRef.value.scrollHeight
    }
  })
})

const emptyEventMessage = computed(() => {
  if (filterValue2.value) return t('game.event_panel.empty_dual')
  if (filterValue1.value !== 'all') return t('game.event_panel.empty_single')
  return t('game.event_panel.empty_none')
})

function formatEventDate(event: { year: number; month: number }) {
  return `${event.year}${t('common.year')}${event.month}${t('common.month')}`
}

// 构建角色名 -> 颜色映射表。
const avatarColorMap = computed(() => buildAvatarColorMap(worldStore.avatarList))

// 渲染事件内容，高亮角色名。
function renderEventContent(event: GameEvent): string {
  const text = event.content || event.text || ''
  return highlightAvatarNames(text, avatarColorMap.value)
}

// 处理事件列表中的点击，使用事件委托检测角色名点击。
function handleEventListClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  const avatarId = target.dataset?.avatarId
  if (avatarId) {
    uiStore.select('avatar', avatarId)
  }
}
</script>

<template>
  <section class="sidebar-section">
    <div class="sidebar-header">
      <h3>{{ t('game.event_panel.title') }}</h3>
      <div class="filter-group">
        <n-select
          v-model:value="filterValue1"
          :options="filterOptions"
          :render-label="renderLabel"
          size="tiny"
          class="event-filter"
        />
        <!-- 双人筛选 -->
        <template v-if="filterValue2 !== null">
          <n-select
            v-model:value="filterValue2"
            :options="filterOptions2"
            :render-label="renderLabel"
            size="tiny"
            class="event-filter"
          />
          <n-button size="tiny" quaternary @click="removeSecondFilter" class="remove-btn">
            &times;
          </n-button>
        </template>
        <!-- 添加第二人按钮（仅当选择了单人时显示） -->
        <n-button
          v-else-if="filterValue1 !== 'all'"
          size="tiny"
          quaternary
          @click="addSecondFilter"
          class="add-btn"
        >
          {{ t('game.event_panel.add_second') }}
        </n-button>
      </div>
    </div>
    <div v-if="worldStore.eventsLoading && displayEvents.length === 0" class="loading">
      <n-spin size="small" />
      <span>{{ t('common.loading') }}</span>
    </div>
    <div v-else-if="displayEvents.length === 0" class="empty">{{ emptyEventMessage }}</div>
    <div v-else class="event-list" ref="eventListRef" @scroll="handleScroll" @click="handleEventListClick">
      <!-- 顶部加载指示器 -->
      <div v-if="worldStore.eventsHasMore" class="load-more-hint">
        <span v-if="worldStore.eventsLoading">{{ t('common.loading') }}</span>
        <span v-else>{{ t('game.event_panel.load_more') }}</span>
      </div>
      <div v-for="event in displayEvents" :key="event.id" class="event-item">
        <div class="event-date">{{ formatEventDate(event) }}</div>
        <div class="event-content" v-html="renderEventContent(event)"></div>
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

.filter-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.event-filter {
  width: 120px;
}

.add-btn {
  color: #888;
  font-size: 11px;
  white-space: nowrap;
}

.add-btn:hover {
  color: #aaa;
}

.remove-btn {
  color: #888;
  font-size: 16px;
  padding: 0 4px;
}

.remove-btn:hover {
  color: #f66;
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

/* 可点击的角色名样式 */
.event-content :deep(.clickable-avatar) {
  cursor: pointer;
  transition: opacity 0.15s;
}

.event-content :deep(.clickable-avatar:hover) {
  opacity: 0.8;
  text-decoration: underline;
}
</style>