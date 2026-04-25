import { computed, h, nextTick, onMounted, ref, watch } from 'vue'
import type { Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { SelectOption } from 'naive-ui'
import { useAvatarStore } from '@/stores/avatar'
import { useEventStore } from '@/stores/event'
import { useRoleplayStore } from '@/stores/roleplay'
import { useUiStore } from '@/stores/ui'
import { useMapStore } from '@/stores/map'
import { useSectStore } from '@/stores/sect'
import type { GameEvent } from '@/types/core'
import type { FetchEventsParams } from '@/types/api'
import {
  avatarIdToColor,
  buildAvatarColorMap,
  buildSectColorMap,
  tokenizeEventContent,
  type EventContentToken,
} from '@/utils/eventHelper'
import { prependAllOption } from '@/utils/selectOptions'

export function useEventPanel() {
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
      value: avatar.id,
    })),
  ])

  const sectFilterOptions = computed(() => {
    return prependAllOption(
      sectStore.activeSectOptions,
      t('game.event_panel.filter_all_sects'),
      'game.event_panel.filter_all_sects',
      '所有宗门',
      'all',
    )
  })

  const majorFilterOptions = computed(() => [
    { label: t('game.event_panel.filter_event_scope_all'), value: 'all' },
    { label: t('game.event_panel.filter_event_scope_major'), value: 'major' },
    { label: t('game.event_panel.filter_event_scope_minor'), value: 'minor' },
  ])

  const panelTitle = computed(() => t('game.event_panel.title'))
  const displayEvents = computed(() => eventStore.events || [])

  function renderLabel(option: SelectOption) {
    if (option.value === 'all') return option.label as string

    const color = avatarIdToColor(option.value as string)
    return h('div', { style: { display: 'flex', alignItems: 'center', gap: '6px' } }, [
      h('span', {
        style: {
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: color,
          flexShrink: 0,
        },
      }),
      option.label as string,
    ])
  }

  function buildFilter() {
    const params: FetchEventsParams = {}
    if (filterValue1.value !== 'all') {
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

  function handleScroll(e: Event) {
    const el = e.target as HTMLElement
    if (!el) return

    if (el.scrollTop < 100 && eventStore.eventsHasMore && !eventStore.eventsLoading) {
      const oldScrollHeight = el.scrollHeight
      eventStore.loadMoreEvents().then(() => {
        nextTick(() => {
          const newScrollHeight = el.scrollHeight
          el.scrollTop = newScrollHeight - oldScrollHeight + el.scrollTop
        })
      })
    }
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
    { immediate: true },
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
    { deep: true },
  )

  watch(filterSectValue, async (newVal) => {
    if (suppressFilterWatch.value) return
    if (controlledAvatarId.value) {
      roleplayAutoApplied.value = false
    }
    if (newVal !== 'all') {
      filterValue1.value = 'all'
    }
    await reloadEvents()
  })

  watch(filterValue1, async (newVal) => {
    if (suppressFilterWatch.value) return
    if (controlledAvatarId.value) {
      roleplayAutoApplied.value = false
    }
    if (newVal !== 'all') {
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
    { immediate: true },
  )

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

  const avatarColorMap = computed(() => buildAvatarColorMap(avatarStore.avatarList))
  const sectColorMap = computed(() => buildSectColorMap(
    Array.from(mapStore.regions.values())
      .filter(region => region.type === 'sect')
      .map(region => ({
        sect_id: region.sect_id,
        sect_name: region.sect_name,
        sect_color: region.sect_color,
      })),
  ))

  watch([avatarColorMap, sectColorMap, locale as Ref<string>], () => {
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

  return {
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
  }
}
