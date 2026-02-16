import { defineStore } from 'pinia';
import { ref, shallowRef } from 'vue';
import type { GameEvent } from '../types/core';
import type { FetchEventsParams } from '../types/api';
import { eventApi } from '../api';
import { processNewEvents, mergeAndSortEvents } from '../utils/eventHelper';

export const useEventStore = defineStore('event', () => {
  const events = shallowRef<GameEvent[]>([]);

  // 分页状态
  const eventsCursor = ref<string | null>(null);
  const eventsHasMore = ref(false);
  const eventsLoading = ref(false);
  const eventsFilter = ref<FetchEventsParams>({});

  // 请求计数器
  let eventsRequestId = 0;

  function addEvents(rawEvents: any[], currentYear: number, currentMonth: number) {
    if (!rawEvents || rawEvents.length === 0) return;

    let newEvents = processNewEvents(rawEvents, currentYear, currentMonth);

    // 根据当前筛选条件过滤（数据在 SQLite 中不会丢失）
    const filter = eventsFilter.value;
    if (filter.avatar_id) {
      newEvents = newEvents.filter(e =>
        e.relatedAvatarIds?.includes(filter.avatar_id!)
      );
    } else if (filter.avatar_id_1 && filter.avatar_id_2) {
      newEvents = newEvents.filter(e =>
        e.relatedAvatarIds?.includes(filter.avatar_id_1!) &&
        e.relatedAvatarIds?.includes(filter.avatar_id_2!)
      );
    }

    if (newEvents.length === 0) return;

    // 使用通用合并排序函数，确保顺序正确（基于 createdAt 或时间戳）
    events.value = mergeAndSortEvents(events.value, newEvents);
  }

  async function loadEvents(filter: FetchEventsParams = {}, append = false) {
    if (eventsLoading.value) return;
    
    // 每次请求增加计数器，只接受最新请求的响应。
    const currentRequestId = ++eventsRequestId;
    eventsLoading.value = true;

    try {
      const params: FetchEventsParams = { ...filter, limit: 100 };
      if (append && eventsCursor.value) {
        params.cursor = eventsCursor.value;
      }

      const res = await eventApi.fetchEvents(params);

      // 如果不是最新请求，丢弃响应。
      if (currentRequestId !== eventsRequestId) {
        return;
      }

      // 转换为 GameEvent 格式
      const newEvents: GameEvent[] = res.events.map(e => ({
        id: e.id,
        text: e.text,
        content: e.content,
        year: e.year,
        month: e.month,
        timestamp: e.month_stamp,
        monthStamp: e.month_stamp,
        relatedAvatarIds: e.related_avatar_ids,
        isMajor: e.is_major,
        isStory: e.is_story,
        createdAt: e.created_at,
      }));

      // API 返回倒序（最新在前），反转成时间正序（最旧在前，最新在后）
      const sortedNewEvents = newEvents.reverse();

      if (append) {
        // 加载更旧的事件，添加到顶部。
        events.value = [...sortedNewEvents, ...events.value];
      } else {
        // 切换筛选条件：直接用 API 数据替换。
        events.value = sortedNewEvents;
        eventsFilter.value = filter;
      }

      eventsCursor.value = res.next_cursor;
      eventsHasMore.value = res.has_more;
    } catch (e) {
      // 如果不是最新请求，不处理错误。
      if (currentRequestId !== eventsRequestId) {
        return;
      }
      console.error('Failed to load events', e);
    } finally {
      // 只有最新请求才更新 loading 状态。
      if (currentRequestId === eventsRequestId) {
        eventsLoading.value = false;
      }
    }
  }

  async function loadMoreEvents() {
    if (!eventsHasMore.value || eventsLoading.value) return;
    await loadEvents(eventsFilter.value, true);
  }

  async function resetEvents(filter: FetchEventsParams = {}) {
    // 使旧请求失效，允许新请求。
    eventsRequestId++;
    eventsLoading.value = false;
    eventsCursor.value = null;
    eventsHasMore.value = false;
    events.value = [];  // 清空旧数据，避免筛选切换时显示残留。
    eventsFilter.value = filter;  // 立即更新筛选条件，让 addEvents 也能正确过滤。
    await loadEvents(filter, false);
  }

  function reset() {
    events.value = [];
    eventsCursor.value = null;
    eventsHasMore.value = false;
    eventsFilter.value = {};
    eventsRequestId++; // Cancel pending requests
    eventsLoading.value = false;
  }

  return {
    events,
    eventsCursor,
    eventsHasMore,
    eventsLoading,
    eventsFilter,
    addEvents,
    loadEvents,
    loadMoreEvents,
    resetEvents,
    reset
  };
});
