import type {
  HoverResponse,
  HoverTarget,
  InitialStateResponse,
  MapResponse,
  IAvatarDetail,
  DetailInfo
} from '../types/game'
import { apiGet, apiPost } from './apiClient'

function buildHoverQuery(target: HoverTarget) {
  const query = new URLSearchParams({
    type: target.type,
    id: target.id
  })
  return `/api/hover?${query.toString()}`
}

function buildDetailQuery(target: HoverTarget) {
  const query = new URLSearchParams({
    type: target.type,
    id: target.id
  })
  return `/api/detail?${query.toString()}`
}

export interface SaveFile {
  filename: string
  save_time: string
  game_time: string
  version: string
}

export const gameApi = {
  getInitialState() {
    return apiGet<InitialStateResponse>('/api/state')
  },

  getHoverInfo(target: HoverTarget) {
    return apiGet<HoverResponse>(buildHoverQuery(target))
  },

  getDetailInfo(target: HoverTarget) {
    return apiGet<DetailInfo>(buildDetailQuery(target))
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
  },
  
  // --- 游戏控制 API ---
  
  pauseGame() {
    return apiPost<{ status: string; message: string }>('/api/control/pause', {})
  },
  
  resumeGame() {
    return apiPost<{ status: string; message: string }>('/api/control/resume', {})
  },

  // --- 存读档 API ---

  getSaves() {
    return apiGet<{ saves: SaveFile[] }>('/api/saves')
  },

  saveGame(filename?: string) {
    return apiPost<{ status: string; filename: string }>('/api/game/save', {
      filename
    })
  },

  loadGame(filename: string) {
    return apiPost<{ status: string; message: string }>('/api/game/load', {
      filename
    })
  }
}
