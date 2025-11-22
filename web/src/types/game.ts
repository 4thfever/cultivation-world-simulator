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

// --- Structured Info Types ---

export interface IEffectEntity {
  name: string;
  desc?: string;
  effect_desc?: string;
  grade?: string;
  rarity?: string;
  type?: string;
  // some entities might have custom fields
  [key: string]: any;
}

export interface ISectInfo extends IEffectEntity {
  alignment: string;
  style: string;
  hq_name: string;
  hq_desc: string;
  rank: string;
}

export interface IItemInfo extends IEffectEntity {
  count: number;
}

export interface IRelationInfo {
  target_id: string;
  name: string;
  relation: string;
  realm: string;
  sect: string;
}

export interface IAvatarDetail {
  id: string;
  name: string;
  gender: string;
  age: number;
  lifespan: number;
  realm: string;
  level: number;
  hp: { cur: number; max: number };
  mp: { cur: number; max: number };
  alignment: string;
  alignment_detail?: IEffectEntity;
  magic_stone: number;
  thinking: string;
  short_term_objective: string;
  long_term_objective: string;
  nickname?: string;
  
  personas: IEffectEntity[];
  technique?: IEffectEntity;
  sect?: ISectInfo;
  weapon?: IEffectEntity & { proficiency: string };
  auxiliary?: IEffectEntity;
  items: IItemInfo[];
  relations: IRelationInfo[];
  appearance: string;
  root: string;
  root_detail?: IEffectEntity;
  spirit_animal?: IEffectEntity;
  
  // Fallback for non-avatar targets or legacy
  fallback?: boolean;
  lines?: unknown; // HoverLines
}

export interface IRegionDetail {
  id: string | number;
  name: string;
  desc: string;
  type: string;
  type_name: string;
  
  animals?: IEffectEntity[];
  plants?: IEffectEntity[];
  essence?: { type: string; density: number };
  
  fallback?: boolean;
  lines?: unknown;
}

export type DetailInfo = IAvatarDetail | IRegionDetail;
