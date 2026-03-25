<script setup lang="ts">
import { computed, ref, watch, nextTick, h, onMounted } from 'vue'
import { useAvatarStore } from '../../../stores/avatar'
import { useEventStore } from '../../../stores/event'
import { useUiStore } from '../../../stores/ui'
import { useMapStore } from '../../../stores/map'
import { useSectStore } from '../../../stores/sect'
import { NSelect, NSpin } from 'naive-ui'
import type { SelectOption } from 'naive-ui'
import { tokenizeEventContent, buildAvatarColorMap, buildSectColorMap, avatarIdToColor } from '../../../utils/eventHelper'
import { prependAllOption } from '../../../utils/selectOptions'
import type { GameEvent } from '../../../types/core'
import type { FetchEventsParams } from '../../../types/api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const avatarStore = useAvatarStore()
const eventStore = useEventStore()
const uiStore = useUiStore()
const mapStore = useMapStore()
const sectStore = useSectStore()

const filterValue1 = ref('all')
const filterSectValue = ref<number | 'all'>('all')
const filterMajorScope = ref<FetchEventsParams['major_scope']>('all')
const eventListRef = ref<HTMLElement | null>(null)

const filterOptions = computed(() => [
  { label: t('game.event_panel.filter_all'), value: 'all' },
  ...avatarStore.avatarList.map(avatar => ({
    label: (avatar.name ?? avatar.id) + (avatar.is_dead ? ` ${t('game.event_panel.deceased')}` : ''),
    value: avatar.id
  }))
])

const sectFilterOptions = computed(() => {
  return prependAllOption(
    sectStore.activeSectOptions,
    t('game.event_panel.filter_all_sects'),
    'game.event_panel.filter_all_sects',
    '所有宗门',
    'all'
  )
})

const majorFilterOptions = computed(() => [
  { label: t('game.event_panel.filter_event_scope_all'), value: 'all' },
  { label: t('game.event_panel.filter_event_scope_major'), value: 'major' },
  { label: t('game.event_panel.filter_event_scope_minor'), value: 'minor' },
])

// 直接使用 store 中的事件（已由 API 过滤）
const displayEvents = computed(() => eventStore.events || [])

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
  if (el.scrollTop < 100 && eventStore.eventsHasMore && !eventStore.eventsLoading) {
    const oldScrollHeight = el.scrollHeight
    eventStore.loadMoreEvents().then(() => {
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
  const params: FetchEventsParams = {}
  if (filterValue1.value !== 'all') {
    // 单人筛选
    params.avatar_id = filterValue1.value
  }
  
  if (filterSectValue.value !== 'all') {
    params.sect_id = filterSectValue.value
  }

  if (filterMajorScope.value && filterMajorScope.value !== 'all') {
    params.major_scope = filterMajorScope.value
  }
  
  return params
}

// 加载事件并滚动到底部
async function reloadEvents() {
  await eventStore.resetEvents(buildFilter())
  nextTick(() => {
    if (eventListRef.value) {
      eventListRef.value.scrollTop = eventListRef.value.scrollHeight
    }
  })
}

onMounted(() => {
  if (!sectStore.isLoaded && mapStore.isLoaded) {
    void sectStore.refreshTerritories()
  }
})

watch(
  () => mapStore.isLoaded,
  (isLoaded) => {
    if (isLoaded && !sectStore.isLoaded && !sectStore.isLoading) {
      void sectStore.refreshTerritories()
    }
  },
  { immediate: true }
)

watch(
  () => sectStore.activeSectOptions,
  (options) => {
    if (filterSectValue.value === 'all') return
    const stillExists = options.some(option => option.value === filterSectValue.value)
    if (!stillExists) {
      filterSectValue.value = 'all'
    }
  },
  { deep: true }
)

// 切换宗门筛选
watch(filterSectValue, async (newVal) => {
  if (newVal !== 'all') {
    // 选了宗门，清空角色的过滤条件
    filterValue1.value = 'all'
  }
  await reloadEvents()
})

// 切换第一人筛选
watch(filterValue1, async (newVal) => {
  if (newVal !== 'all') {
    // 选了角色，清空宗门的过滤条件
    filterSectValue.value = 'all'
  }
  await reloadEvents()
})

watch(filterMajorScope, async () => {
  await reloadEvents()
})

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

const emptyEventMessage = computed(() => {
  if (filterValue1.value !== 'all') return t('game.event_panel.empty_single')
  return t('game.event_panel.empty_none')
})

function formatEventDate(event: { year: number; month: number }) {
  return `${event.year}${t('common.year')}${event.month}${t('common.month')}`
}

// 构建角色名 -> 颜色映射表。
const avatarColorMap = computed(() => buildAvatarColorMap(avatarStore.avatarList))
const sectColorMap = computed(() => buildSectColorMap(
  Array.from(mapStore.regions.values())
    .filter(region => region.type === 'sect')
    .map(region => ({
      sect_id: region.sect_id,
      sect_name: region.sect_name,
      sect_color: region.sect_color,
    }))
))

// 渲染事件内容：拆分为安全 token，避免使用 v-html。
function renderEventContent(event: GameEvent) {
  const text = event.renderKey
    ? t(`game.event_templates.${event.renderKey}`, event.renderParams ?? {})
    : (event.content || event.text || '')
  return tokenizeEventContent(text, avatarColorMap.value, sectColorMap.value)
}

function handleAvatarClick(avatarId?: string) {
  if (avatarId) {
    uiStore.select('avatar', avatarId)
  }
}

function handleSectClick(sectId?: number) {
  if (sectId != null) {
    uiStore.select('sect', String(sectId))
  }
}
</script>

<template>
  <section class="sidebar-section">
    <div class="sidebar-header">
      <h3>{{ t('game.event_panel.title') }}</h3>
      <div class="filter-group">
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
      <div v-for="event in displayEvents" :key="event.id" class="event-item">
        <div class="event-date">{{ formatEventDate(event) }}</div>
        <div class="event-content">
          <template v-for="(segment, index) in renderEventContent(event)" :key="`${event.id}-${index}`">
            <span
              v-if="segment.type === 'avatar'"
              class="clickable-avatar"
              :style="{ color: segment.color }"
              @click="handleAvatarClick(segment.avatarId)"
            >
              {{ segment.text }}
            </span>
            <span
              v-else-if="segment.type === 'sect'"
              class="clickable-sect"
              :style="{ color: segment.color }"
              @click="handleSectClick(segment.sectId)"
            >
              {{ segment.text }}
            </span>
            <span v-else>{{ segment.text }}</span>
          </template>
        </div>
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

.event-content :deep(.clickable-sect) {
  cursor: pointer;
  transition: opacity 0.15s;
}

.event-content :deep(.clickable-avatar:hover),
.event-content :deep(.clickable-sect:hover) {
  opacity: 0.8;
  text-decoration: underline;
}
</style>
