import type {
  HoverResponse,
  HoverTarget,
  InitialStateResponse,
  MapResponse
} from '../types/game'
import { apiGet } from './apiClient'

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
  }
}

