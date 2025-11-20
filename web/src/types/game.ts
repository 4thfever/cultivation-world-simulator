export type HoverSegment = {
  text: string
  color?: string
}

export type HoverLine = HoverSegment[]

export interface HoverTarget {
  type: 'avatar' | 'region'
  id: string
  name?: string
}

export interface Avatar {
  id: string
  name?: string
  x: number
  y: number
  action?: string
  gender?: string
  pic_id?: number
}

export interface GameEvent {
  id: string
  text: string
  content?: string
  year?: number
  month?: number
  monthStamp?: number
  relatedAvatarIds: string[]
  isMajor?: boolean
  isStory?: boolean
}

export interface TickPayload {
  type: 'tick'
  year: number
  month: number
  avatars?: Avatar[]
  events?: unknown[]
}

export interface InitialStateResponse {
  status: 'ok' | 'error'
  year: number
  month: number
  avatars?: Avatar[]
  events?: unknown[]
}

export interface HoverResponse {
  lines: unknown
}

export type MapMatrix = string[][]

export interface Region {
  id: string | number
  name: string
  x: number
  y: number
  type: string
  sect_name?: string
}

export interface MapResponse {
  data: MapMatrix
  regions: Region[]
}

