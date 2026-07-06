<script setup lang="ts">
import type { EventSubject, GameEvent } from '@/types/core'

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

const MAX_VISIBLE_SUBJECTS = 3

function visibleSubjects(event: GameEvent): EventSubject[] {
  return eventSubjects(event).slice(0, MAX_VISIBLE_SUBJECTS)
}

function hiddenSubjectCount(event: GameEvent): number {
  return Math.max(0, eventSubjects(event).length - MAX_VISIBLE_SUBJECTS)
}

function eventSubjects(event: GameEvent): EventSubject[] {
  return Array.isArray(event.subjects) ? event.subjects : []
}

function subjectStyle(subject: EventSubject) {
  if (subject.type === 'avatar') {
    return { color: subject.color || undefined }
  }
  return { color: subject.color || undefined, borderColor: subject.color || undefined }
}

function subjectTitle(event: GameEvent): string {
  return eventSubjects(event).map(subject => subject.name).join('、')
}

function handleSubjectClick(subject: EventSubject) {
  if (subject.type === 'avatar') {
    props.onAvatarClick?.(subject.id)
    return
  }
  props.onSectClick?.(subject.id)
}
</script>

<template>
  <div class="event-stream-list">
    <div v-if="events.length === 0" class="event-stream-list__empty">{{ emptyText }}</div>
    <div v-for="event in events" :key="event.id" class="event-stream-list__row">
      <span class="event-stream-list__date">{{ formatDate(event) }}</span>
      <div class="event-stream-list__body">
        <div class="event-stream-list__main">
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
            <span
              v-if="eventSubjects(event).length > 0"
              class="event-stream-list__subjects"
              :title="subjectTitle(event)"
            >
              <button
                v-for="subject in visibleSubjects(event)"
                :key="`${event.id}-${subject.type}-${subject.id}`"
                type="button"
                class="event-stream-list__subject"
                :class="{
                  'event-stream-list__subject--avatar': subject.type === 'avatar',
                  'event-stream-list__subject--sect': subject.type === 'sect',
                  'event-stream-list__subject--dead': subject.type === 'avatar' && subject.isDead,
                  'clickable-avatar': subject.type === 'avatar',
                  'clickable-sect': subject.type === 'sect',
                }"
                :style="subjectStyle(subject)"
                @click="handleSubjectClick(subject)"
              >
                {{ subject.name }}
              </button>
              <span
                v-if="hiddenSubjectCount(event) > 0"
                class="event-stream-list__subject event-stream-list__subject--more"
              >
                +{{ hiddenSubjectCount(event) }}
              </span>
            </span>
            <span v-else class="event-stream-list__subjects">
              <span class="event-stream-list__subject event-stream-list__subject--world">世界</span>
            </span>
          </div>
        </div>
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
  padding: 5px 0;
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

.event-stream-list__body {
  flex: 1;
  min-width: 0;
}

.event-stream-list__main {
  min-width: 0;
}

.event-stream-list__subjects {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  min-width: 0;
  flex-wrap: wrap;
  margin-left: 6px;
  vertical-align: text-bottom;
}

.event-stream-list__subject {
  display: inline-flex;
  align-items: center;
  max-width: 92px;
  height: 18px;
  padding: 0 5px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  color: #d8d8d8;
  font-size: 12px;
  line-height: 16px;
  vertical-align: text-bottom;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

button.event-stream-list__subject {
  font: inherit;
}

.event-stream-list__subject--sect {
  background: rgba(255, 255, 255, 0.04);
}

.event-stream-list__subject--dead {
  opacity: 0.72;
}

.event-stream-list__subject--more,
.event-stream-list__subject--world {
  cursor: default;
  color: #aaa;
}

.event-stream-list__content,
.event-stream-list__empty {
  font-size: 13px;
  line-height: 1.6;
}

.event-stream-list__content {
  color: #ddd;
  width: 100%;
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
