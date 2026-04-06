import { httpClient } from '../http';
import type { 
  EventsResponseDTO,
  FetchEventsParams
} from '../../types/api';
import { normalizeEventsResponse } from '../mappers/event';

export const eventApi = {
  async fetchEvents(params: FetchEventsParams = {}) {
    const query = new URLSearchParams();
    if (params.avatar_id) query.set('avatar_id', params.avatar_id);
    if (params.avatar_id_1) query.set('avatar_id_1', params.avatar_id_1);
    if (params.avatar_id_2) query.set('avatar_id_2', params.avatar_id_2);
    if (params.sect_id != null) query.set('sect_id', String(params.sect_id));
    if (params.major_scope && params.major_scope !== 'all') query.set('major_scope', params.major_scope);
    if (params.cursor) query.set('cursor', params.cursor);
    if (params.limit) query.set('limit', String(params.limit));
    const qs = query.toString();
    const data = await httpClient.get<EventsResponseDTO>(`/api/v1/query/events${qs ? '?' + qs : ''}`);
    return normalizeEventsResponse(data);
  },

  cleanupEvents(keepMajor = true, beforeMonthStamp?: number) {
    const query = new URLSearchParams();
    query.set('keep_major', String(keepMajor));
    if (beforeMonthStamp !== undefined) query.set('before_month_stamp', String(beforeMonthStamp));
    return httpClient.delete<{ deleted: number }>(`/api/v1/command/events/cleanup?${query}`);
  }
};
