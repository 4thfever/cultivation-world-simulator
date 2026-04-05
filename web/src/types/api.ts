/**
 * API 数据传输对象 (Data Transfer Objects)
 * 这些类型严格对应后端接口返回的 JSON 结构。
 */

import type { AppLocale } from '../locales/registry';
import type {
  MapMatrix,
  CelestialPhenomenon,
  HiddenDomainInfo,
  AvatarDetail,
  RegionDetail,
  SectDetail,
  EffectEntity,
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

export interface AvatarAdjustOptionDTO extends EffectEntity {
  id: string;
}

export interface AvatarAdjustCatalogDTO {
  techniques: AvatarAdjustOptionDTO[];
  weapons: AvatarAdjustOptionDTO[];
  auxiliaries: AvatarAdjustOptionDTO[];
  personas: AvatarAdjustOptionDTO[];
  goldfingers: AvatarAdjustOptionDTO[];
}

export interface UpdateAvatarAdjustmentParams {
  avatar_id: string;
  category: 'technique' | 'weapon' | 'auxiliary' | 'personas' | 'goldfinger';
  target_id?: number | null;
  persona_ids?: number[];
}

export interface UpdateAvatarPortraitParams {
  avatar_id: string;
  pic_id: number;
}

export interface GenerateCustomContentParams {
  category: 'technique' | 'weapon' | 'auxiliary' | 'goldfinger';
  realm?: string;
  user_prompt: string;
}

export interface CustomContentDraftDTO extends AvatarAdjustOptionDTO {
  category: 'technique' | 'weapon' | 'auxiliary' | 'goldfinger';
  realm?: string;
  effects: Record<string, number | boolean>;
  weapon_type?: string;
  display_text?: string;
  story_prompt?: string;
  mechanism_type?: string;
  is_custom?: boolean;
}

export interface CreateCustomContentParams {
  category: 'technique' | 'weapon' | 'auxiliary' | 'goldfinger';
  draft: CustomContentDraftDTO;
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

export interface AudioSettingsDTO {
  bgm_volume: number;
  sfx_volume: number;
}

export interface UISettingsDTO {
  locale: AppLocale | string;
  audio: AudioSettingsDTO;
}

export interface SimulationSettingsDTO {
  auto_save_enabled: boolean;
  max_auto_saves: number;
}

export interface LLMConfigViewDTO {
  base_url: string;
  model_name: string;
  fast_model_name: string;
  mode: string;
  max_concurrent_requests: number;
  has_api_key: boolean;
  api_format: string;
}

export interface LLMConfigDTO {
  base_url: string;
  api_key?: string;
  model_name: string;
  fast_model_name: string;
  mode: string;
  max_concurrent_requests: number;
  clear_api_key?: boolean;
  api_format: string;
}

export interface RunConfigDTO {
  content_locale: AppLocale | string;
  init_npc_num: number;
  sect_num: number;
  npc_awakening_rate_per_month: number;
  world_lore?: string;
}

export interface AppSettingsDTO {
  schema_version: number;
  ui: UISettingsDTO;
  simulation: SimulationSettingsDTO;
  llm: {
    profile: LLMConfigViewDTO;
  };
  new_game_defaults: RunConfigDTO;
}

export interface AppSettingsPatchDTO {
  ui?: {
    locale?: UISettingsDTO['locale'];
    audio?: Partial<AudioSettingsDTO>;
  };
  simulation?: Partial<SimulationSettingsDTO>;
  new_game_defaults?: Partial<RunConfigDTO>;
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
  render_key?: string;
  render_params?: Record<string, string | number | boolean | null>;
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
  major_scope?: 'all' | 'major' | 'minor';
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

export interface SectTerritorySummaryDTO {
  id: number;
  name: string;
  color: string;
  influence_radius: number;
  is_active: boolean;
  owned_tiles: Array<{
    x: number;
    y: number;
  }>;
  boundary_edges: Array<{
    x: number;
    y: number;
    side: 'left' | 'right' | 'top' | 'bottom' | string;
  }>;
}

export interface SectTerritoriesResponseDTO {
  sects: SectTerritorySummaryDTO[];
}

export interface TrackedMortalDTO {
  id: string;
  name: string;
  gender: string;
  age: number;
  born_region_id: number;
  born_region_name: string;
  parents: string[];
  is_awakening_candidate: boolean;
}

export interface MortalCityOverviewDTO {
  id: number;
  name: string;
  population: number;
  population_capacity: number;
  natural_growth: number;
}

export interface MortalOverviewResponseDTO {
  summary: {
    total_population: number;
    total_population_capacity: number;
    total_natural_growth: number;
    tracked_mortal_count: number;
    awakening_candidate_count: number;
  };
  cities: MortalCityOverviewDTO[];
  tracked_mortals: TrackedMortalDTO[];
}

export interface DynastyOverviewResponseDTO {
  name: string;
  title: string;
  royal_surname: string;
  royal_house_name: string;
  desc: string;
  effect_desc: string;
  style_tag: string;
  official_preference_label: string;
  is_low_magic: boolean;
  current_emperor?: {
    name: string;
    surname: string;
    given_name: string;
    age: number;
    max_age: number;
    is_mortal: boolean;
  } | null;
}

export interface DynastyOfficialDTO {
  id: string;
  name: string;
  realm: string;
  official_rank_key: string;
  official_rank_name: string;
  court_reputation: number;
  sect_name: string;
}

export interface DynastyDetailResponseDTO {
  overview: DynastyOverviewResponseDTO;
  summary: {
    official_count: number;
    top_official_rank_name: string;
  };
  officials: DynastyOfficialDTO[];
}

export type ToastLevel = 'error' | 'warning' | 'success' | 'info' | string;
export type AppLanguage = AppLocale | string;

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
