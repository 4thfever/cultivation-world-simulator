import type { EventDTO } from '@/types/api'
import type { EventSubject, GameEvent } from '@/types/core'
import { avatarIdToColor } from '@/utils/eventHelper'

export interface EventPage {
  events: EventDTO[]
  nextCursor: string | null
  hasMore: boolean
}

export function mapEventDtoToGameEvent(event: EventDTO): GameEvent {
  return {
    id: event.id,
    text: event.text,
    content: event.content,
    year: event.year,
    month: event.month,
    timestamp: event.month_stamp,
    relatedAvatarIds: event.related_avatar_ids,
    relatedSects: event.related_sects,
    subjects: mapEventSubjects(event.subjects),
    isMajor: event.is_major,
    isStory: event.is_story,
    renderKey: event.render_key,
    renderParams: event.render_params,
    createdAt: event.created_at,
  }
}

export function mapEventSubjects(subjects: EventDTO['subjects']): EventSubject[] {
  if (!Array.isArray(subjects)) return []
  return subjects.map((subject) => {
    if (subject.type === 'sect') {
      return {
        type: 'sect',
        id: subject.id,
        name: subject.name,
        color: subject.color,
        isActive: subject.is_active,
      }
    }
    return {
      type: 'avatar',
      id: subject.id,
      name: subject.name,
      color: subject.color || avatarIdToColor(subject.id),
      isDead: subject.is_dead,
    }
  })
}

export function mapEventDtosToTimeline(events: EventDTO[]): GameEvent[] {
  // API returns newest-first; timeline UI expects oldest-first.
  return events.map(mapEventDtoToGameEvent).reverse()
}

export function normalizeEventsResponse(
  input: { events?: EventDTO[]; next_cursor?: string | null; has_more?: boolean } | null | undefined,
): EventPage {
  return {
    events: Array.isArray(input?.events) ? input.events : [],
    nextCursor: input?.next_cursor ?? null,
    hasMore: input?.has_more ?? false,
  }
}

