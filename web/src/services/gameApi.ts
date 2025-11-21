import type {
  HoverResponse,
  HoverTarget,
  InitialStateResponse,
  MapResponse
} from '../types/game'
import { apiGet, apiPost } from './apiClient'

function buildHoverQuery(target: HoverTarget) {
  const query = new URLSearchParams({
    type: target.type,
    id: target.id
  })
  return `/api/hover?${query.toString()}`
}

export const gameApi = {
  getInitialState() {
    return apiGet<InitialStateResponse>('/api/state')
  },

  getHoverInfo(target: HoverTarget) {
    return apiGet<HoverResponse>(buildHoverQuery(target))
  },

  getMap() {
    return apiGet<MapResponse>('/api/map')
  },

  setLongTermObjective(avatarId: string, content: string) {
    return apiPost<{ status: string; message: string }>('/api/action/set_long_term_objective', {
      avatar_id: avatarId,
      content
    })
  },

  clearLongTermObjective(avatarId: string) {
    return apiPost<{ status: string; message: string }>('/api/action/clear_long_term_objective', {
      avatar_id: avatarId
    })
  }
}
