import type { EventDTO } from '@/types/api'
import type { GameEvent } from '@/types/core'

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
    isMajor: event.is_major,
    isStory: event.is_story,
    renderKey: event.render_key,
    renderParams: event.render_params,
    createdAt: event.created_at,
  }
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

