import { httpClient } from '../http';
import type { 
  EventsResponseDTO,
  FetchEventsParams
} from '../../types/api';

export const eventApi = {
  fetchEvents(params: FetchEventsParams = {}) {
    const query = new URLSearchParams();
    if (params.avatar_id) query.set('avatar_id', params.avatar_id);
    if (params.avatar_id_1) query.set('avatar_id_1', params.avatar_id_1);
    if (params.avatar_id_2) query.set('avatar_id_2', params.avatar_id_2);
    if (params.cursor) query.set('cursor', params.cursor);
    if (params.limit) query.set('limit', String(params.limit));
    const qs = query.toString();
    return httpClient.get<EventsResponseDTO>(`/api/events${qs ? '?' + qs : ''}`);
  },

  cleanupEvents(keepMajor = true, beforeMonthStamp?: number) {
    const query = new URLSearchParams();
    query.set('keep_major', String(keepMajor));
    if (beforeMonthStamp !== undefined) query.set('before_month_stamp', String(beforeMonthStamp));
    return httpClient.delete<{ deleted: number }>(`/api/events/cleanup?${query}`);
  }
};
