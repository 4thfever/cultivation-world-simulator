<script setup lang="ts">
import type { GameEvent } from '@/types/core'

type EventSegment =
  | { type: 'text'; text: string }
  | { type: 'avatar'; text: string; color?: string; avatarId?: string }
  | { type: 'sect'; text: string; color?: string; sectId?: number }

const props = defineProps<{
  events: GameEvent[]
  emptyText: string
  formatDate: (event: GameEvent) => string
  renderSegments?: (event: GameEvent) => EventSegment[]
  onAvatarClick?: (avatarId?: string) => void
  onSectClick?: (sectId?: number) => void
}>()
</script>

<template>
  <div class="event-stream-list">
    <div v-if="events.length === 0" class="event-stream-list__empty">{{ emptyText }}</div>
    <div v-for="event in events" :key="event.id" class="event-stream-list__row">
      <span class="event-stream-list__date">{{ formatDate(event) }}</span>
      <div class="event-stream-list__content">
        <template v-if="renderSegments">
          <template v-for="(segment, index) in renderSegments(event)" :key="`${event.id}-${index}`">
            <span
              v-if="segment.type === 'avatar'"
              class="event-stream-list__link clickable-avatar"
              :style="{ color: segment.color }"
              @click="onAvatarClick?.(segment.avatarId)"
            >
              {{ segment.text }}
            </span>
            <span
              v-else-if="segment.type === 'sect'"
              class="event-stream-list__link clickable-sect"
              :style="{ color: segment.color }"
              @click="onSectClick?.(segment.sectId)"
            >
              {{ segment.text }}
            </span>
            <span v-else>{{ segment.text }}</span>
          </template>
        </template>
        <template v-else>
          {{ event.content || event.text }}
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.event-stream-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.event-stream-list__row {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #2a2a2a;
}

.event-stream-list__row:last-child {
  border-bottom: none;
}

.event-stream-list__date {
  flex: 0 0 76px;
  font-size: 13px;
  color: #999;
  white-space: nowrap;
}

.event-stream-list__content,
.event-stream-list__empty {
  font-size: 13px;
  line-height: 1.6;
}

.event-stream-list__content {
  color: #ddd;
  flex: 1;
  min-width: 0;
  white-space: pre-line;
}

.event-stream-list__empty {
  color: #666;
  text-align: center;
  padding: 10px 0;
}

.event-stream-list__link {
  cursor: pointer;
  transition: opacity 0.15s;
}

.event-stream-list__link:hover {
  opacity: 0.8;
  text-decoration: underline;
}
</style>
