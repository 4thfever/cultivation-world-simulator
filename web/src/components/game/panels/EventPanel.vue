<script setup lang="ts">
import { computed, ref, watch, nextTick, h, onMounted } from 'vue'
import { useAvatarStore } from '../../../stores/avatar'
import { useEventStore } from '../../../stores/event'
import { useRoleplayStore } from '../../../stores/roleplay'
import { useUiStore } from '../../../stores/ui'
import { useMapStore } from '../../../stores/map'
import { useSectStore } from '../../../stores/sect'
import { NSelect, NSpin } from 'naive-ui'
import EventStreamList from '@/components/game/EventStreamList.vue'
import type { SelectOption } from 'naive-ui'
import { tokenizeEventContent, buildAvatarColorMap, buildSectColorMap, avatarIdToColor, type EventContentToken } from '../../../utils/eventHelper'
import { prependAllOption } from '../../../utils/selectOptions'
import type { GameEvent } from '../../../types/core'
import type { FetchEventsParams } from '../../../types/api'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
const avatarStore = useAvatarStore()
const eventStore = useEventStore()
const roleplayStore = useRoleplayStore()
const uiStore = useUiStore()
const mapStore = useMapStore()
const sectStore = useSectStore()

const filterValue1 = ref('all')
const filterSectValue = ref<number | 'all'>('all')
const filterMajorScope = ref<FetchEventsParams['major_scope']>('all')
const eventListRef = ref<HTMLElement | null>(null)
const eventSegmentCache = new Map<string, EventContentToken[]>()
const preRoleplayFilter = ref<{
  avatar: string
  sect: number | 'all'
  majorScope: FetchEventsParams['major_scope']
} | null>(null)
const suppressFilterWatch = ref(false)
const roleplayAutoApplied = ref(false)

const controlledAvatarId = computed(() => roleplayStore.session.controlled_avatar_id ?? '')
const roleplayLockedAvatarName = computed(() => {
  if (!controlledAvatarId.value || !roleplayAutoApplied.value) return ''
  const avatar = avatarStore.avatarList.find(item => item.id === controlledAvatarId.value)
  return avatar?.name ?? controlledAvatarId.value
})

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

const panelTitle = computed(() => t('game.event_panel.title'))

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

async function setFiltersAndReload(params: {
  avatar?: string
  sect?: number | 'all'
  majorScope?: FetchEventsParams['major_scope']
}) {
  suppressFilterWatch.value = true
  if (params.avatar !== undefined) {
    filterValue1.value = params.avatar
  }
  if (params.sect !== undefined) {
    filterSectValue.value = params.sect
  }
  if (params.majorScope !== undefined) {
    filterMajorScope.value = params.majorScope
  }
  await nextTick()
  suppressFilterWatch.value = false
  await reloadEvents()
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
  if (suppressFilterWatch.value) return
  if (controlledAvatarId.value) {
    roleplayAutoApplied.value = false
  }
  if (newVal !== 'all') {
    // 选了宗门，清空角色的过滤条件
    filterValue1.value = 'all'
  }
  await reloadEvents()
})

// 切换第一人筛选
watch(filterValue1, async (newVal) => {
  if (suppressFilterWatch.value) return
  if (controlledAvatarId.value) {
    roleplayAutoApplied.value = false
  }
  if (newVal !== 'all') {
    // 选了角色，清空宗门的过滤条件
    filterSectValue.value = 'all'
  }
  await reloadEvents()
})

watch(filterMajorScope, async () => {
  if (suppressFilterWatch.value) return
  if (controlledAvatarId.value) {
    roleplayAutoApplied.value = false
  }
  await reloadEvents()
})

watch(
  controlledAvatarId,
  async (newAvatarId, oldAvatarId) => {
    if (newAvatarId) {
      if (!oldAvatarId && preRoleplayFilter.value == null) {
        preRoleplayFilter.value = {
          avatar: filterValue1.value,
          sect: filterSectValue.value,
          majorScope: filterMajorScope.value,
        }
      }
      roleplayAutoApplied.value = true
      await setFiltersAndReload({
        avatar: newAvatarId,
        sect: 'all',
      })
      return
    }

    if (oldAvatarId && preRoleplayFilter.value && roleplayAutoApplied.value) {
      const previous = preRoleplayFilter.value
      preRoleplayFilter.value = null
      roleplayAutoApplied.value = false
      await setFiltersAndReload({
        avatar: previous.avatar,
        sect: previous.sect,
        majorScope: previous.majorScope,
      })
      return
    }
    preRoleplayFilter.value = null
    roleplayAutoApplied.value = false
  },
  { immediate: true }
)

// 智能滚动：仅当用户处于底部时才自动跟随滚动（用于实时推送的新事件）。
// 只监听列表边界，避免长事件流下 deep traverse 整个事件对象数组。
watch(() => {
  const events = displayEvents.value
  const lastEvent = events[events.length - 1]
  return `${events.length}:${lastEvent?.id ?? ''}:${lastEvent?.createdAt ?? ''}`
}, () => {
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
})

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

watch([avatarColorMap, sectColorMap, locale], () => {
  eventSegmentCache.clear()
})

function getEventText(event: GameEvent) {
  return event.renderKey
    ? t(`game.event_templates.${event.renderKey}`, event.renderParams ?? {})
    : (event.content || event.text || '')
}

function getEventSegmentCacheKey(event: GameEvent, text: string) {
  return [
    locale.value,
    event.id,
    event.renderKey ?? '',
    JSON.stringify(event.renderParams ?? {}),
    text,
  ].join('\u001f')
}

// 渲染事件内容：拆分为安全 token，避免使用 v-html。
function renderEventContent(event: GameEvent) {
  const text = getEventText(event)
  const cacheKey = getEventSegmentCacheKey(event, text)
  const cached = eventSegmentCache.get(cacheKey)
  if (cached) return cached

  const tokens = tokenizeEventContent(text, avatarColorMap.value, sectColorMap.value)
  eventSegmentCache.set(cacheKey, tokens)
  return tokens
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
