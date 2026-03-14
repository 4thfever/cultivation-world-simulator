/**
 * API 数据传输对象 (Data Transfer Objects)
 * 这些类型严格对应后端接口返回的 JSON 结构。
 */

import type {
  MapMatrix,
  CelestialPhenomenon,
  HiddenDomainInfo,
  AvatarDetail,
  RegionDetail,
  SectDetail,
} from './core';

// --- 通用响应 ---

export interface ApiResponse<T> {
  status: 'ok' | 'error';
  message?: string;
  data?: T; // 有些接口直接把数据铺平在顶层，需根据实际情况调整
}

// --- 具体接口响应 ---

export interface InitialStateDTO {
  status: 'ok' | 'error';
  year: number;
  month: number;
  avatars?: Array<{
    id: string;
    name?: string;
    x: number;
    y: number;
    action?: string;
    gender?: string;
    pic_id?: number;
  }>;
  events?: EventDTO[];
  phenomenon?: CelestialPhenomenon | null;
}

export interface TickPayloadDTO {
  type: 'tick';
  year: number;
  month: number;
  avatars?: Array<Partial<InitialStateDTO['avatars'] extends (infer U)[] ? U : never>>;
  events?: EventDTO[];
  phenomenon?: CelestialPhenomenon | null;
  active_domains?: HiddenDomainInfo[];
}

export interface MapResponseDTO {
  data: MapMatrix;
  regions: Array<{
    id: string | number;
    name: string;
    x: number;
    y: number;
    type: string;
    sect_id?: number;
    sect_name?: string;
    sect_is_active?: boolean;
    sect_color?: string;
    sub_type?: string;
  }>;
  config?: FrontendConfigDTO;
}

// --- Detail 接口 ---

// 目前后端 /api/detail 直接返回 Avatar/Region/Sect 的结构化信息，
// 在 P0 阶段我们先复用前端领域模型作为 DTO 类型，后续若后端结构调整再拆分。
export type AvatarDetailDTO = AvatarDetail;
export type RegionDetailDTO = RegionDetail;
export type SectDetailDTO = SectDetail;

export type DetailResponseDTO =
  | AvatarDetailDTO
  | RegionDetailDTO
  | SectDetailDTO;

export interface FrontendConfigDTO {
  water_speed?: 'none' | 'low' | 'medium' | 'high';
  cloud_freq?: 'none' | 'low' | 'high';
}

export interface SaveFileDTO {
  filename: string;
  save_time: string;
  game_time: string;
  version: string;
  // 新增字段。
  language: string;
  avatar_count: number;
  alive_count: number;
  dead_count: number;
  custom_name: string | null;
  event_count: number;
  is_auto_save: boolean;
  playthrough_id?: string;
}

// --- Game Data Metadata ---

export interface GameDataDTO {
  sects: Array<{ id: number; name: string; alignment: string }>;
  personas: Array<{ id: number; name: string; desc: string; rarity: string }>;
  realms: string[];
  techniques: Array<{ id: number; name: string; grade: string; attribute: string; sect: string | null }>;
  weapons: Array<{ id: number; name: string; grade: string; type: string }>;
  auxiliaries: Array<{ id: number; name: string; grade: string }>;
  alignments: Array<{ value: string; label: string }>;
}

export interface SimpleAvatarDTO {
  id: string;
  name: string;
  sect_name: string;
  realm: string;
  gender: string;
  age: number;
}

export interface CreateAvatarParams {
  surname?: string;
  given_name?: string;
  gender?: string;
  age?: number;
  level?: number;
  sect_id?: number;
  persona_ids?: number[];
  pic_id?: number;
  technique_id?: number;
  weapon_id?: number;
  auxiliary_id?: number;
  alignment?: string;
  appearance?: number;
  relations?: Array<{ target_id: string; relation: string }>;
}

export interface PhenomenonDTO {
  id: number;
  name: string;
  desc: string;
  rarity: string;
  duration_years: number;
  effect_desc: string;
}

// --- Config ---

export interface LLMConfigDTO {
  base_url: string;
  api_key: string;
  model_name: string;
  fast_model_name: string;
  mode: string;
  max_concurrent_requests?: number;
}

export interface GameStartConfigDTO {
  init_npc_num: number;
  sect_num: number;
  npc_awakening_rate_per_month: number;
  world_history?: string;
}

export interface CurrentConfigDTO {
  game: {
    init_npc_num: number;
    sect_num: number;
    npc_awakening_rate_per_month: number;
    world_history?: string;
  };
  avatar: {};
}

// --- Events ---

export interface EventDTO {
  id: string;
  text: string;
  content: string;
  year: number;
  month: number;
  month_stamp: number;
  related_avatar_ids: string[];
  related_sects?: number[];
  is_major: boolean;
  is_story: boolean;
  created_at: number;
}

export interface EventsResponseDTO {
  events: EventDTO[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface FetchEventsParams {
  avatar_id?: string;
  avatar_id_1?: string;
  avatar_id_2?: string;
  sect_id?: number;
  cursor?: string;
  limit?: number;
}

// --- Status ---

export interface InitStatusDTO {
  status: 'idle' | 'pending' | 'in_progress' | 'ready' | 'error';
  phase: number;
  phase_name: string;
  progress: number;
  elapsed_seconds: number;
  error: string | null;
  version?: string;
  llm_check_failed: boolean;
  llm_error_message: string;
}

export interface RankingAvatarDTO {
  id: string;
  name: string;
  sect: string;
  sect_id?: string;
  realm: string;
  stage: string;
  power: number;
}

export interface RankingSectDTO {
  id: string;
  name: string;
  alignment: string;
  member_count: number;
  total_power: number;
}

export interface TournamentSummaryDTO {
  next_year: number;
  heaven_first?: { id: string; name: string };
  earth_first?: { id: string; name: string };
  human_first?: { id: string; name: string };
}

export interface RankingsDTO {
  heaven: RankingAvatarDTO[];
  earth: RankingAvatarDTO[];
  human: RankingAvatarDTO[];
  sect: RankingSectDTO[];
  tournament?: TournamentSummaryDTO;
}

// --- Sect Relations ---

export interface SectRelationDTO {
  sect_a_id: number;
  sect_a_name: string;
  sect_b_id: number;
  sect_b_name: string;
  value: number;        // -100 ~ 100
  diplomacy_status: 'war' | 'peace' | string;
  diplomacy_duration_months: number;
  reason_breakdown: Array<{
    reason: string;     // 枚举字符串，如 ALIGNMENT_OPPOSITE
    delta: number;      // 本事由对关系值的增减
    meta?: Record<string, unknown>;
  }>;
}

export interface SectRelationsResponseDTO {
  relations: SectRelationDTO[];
}

export type ToastLevel = 'error' | 'warning' | 'success' | 'info' | string;
export type AppLanguage = 'zh-CN' | 'en-US' | string;

export interface ToastSocketMessage {
  type: 'toast';
  level: ToastLevel;
  message: string;
  language?: AppLanguage;
}

export interface LLMConfigRequiredSocketMessage {
  type: 'llm_config_required';
  error?: string;
}

export interface GameReinitializedSocketMessage {
  type: 'game_reinitialized';
  message?: string;
}

export type SocketMessageDTO =
  | TickPayloadDTO
  | ToastSocketMessage
  | LLMConfigRequiredSocketMessage
  | GameReinitializedSocketMessage;
