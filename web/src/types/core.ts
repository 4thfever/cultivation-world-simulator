/**
 * 核心领域模型 (Core Domain Models)
 * 这些类型代表了前端应用内部使用的“标准”数据结构。
 * 它们应该是完整的、经过清洗的数据，尽量减少 undefined 的使用。
 */

// --- 基础实体 ---

export interface EntityBase {
  id: string;
  name: string;
}

export interface Coordinates {
  x: number;
  y: number;
}

// --- 物品与效果 ---

export interface EffectEntity extends EntityBase {
  desc?: string;
  effect_desc?: string;
  grade?: string;
  rarity?: string; // e.g., 'SSR', 'R', '上品'
  type?: string;
  color?: string | number[]; // 某些实体自带颜色
}

export interface Item extends EffectEntity {
  count: number;
}

// --- 角色 (Avatar) ---

export interface AvatarSummary extends EntityBase, Coordinates {
  action?: string;
  gender?: string;
  pic_id?: number;
}

export interface AvatarDetail extends EntityBase {
  // 基础信息
  gender: string;
  age: number;
  lifespan: number;
  nickname?: string;
  appearance: string; // 外貌描述
  
  // 修行状态
  realm: string;
  level: number;
  hp: { cur: number; max: number };
  mp: { cur: number; max: number };
  magic_stone: number;
  
  // 属性与资质
  alignment: string;
  alignment_detail?: EffectEntity;
  root: string;
  root_detail?: EffectEntity;
  
  // 思维与目标
  thinking: string;
  short_term_objective: string;
  long_term_objective: string;
  
  // 关联实体
  sect?: SectInfo;
  personas: EffectEntity[];
  technique?: EffectEntity;
  weapon?: EffectEntity & { proficiency: string };
  auxiliary?: EffectEntity;
  spirit_animal?: EffectEntity;
  
  // 列表数据
  items: Item[];
  relations: RelationInfo[];
}

export interface SectInfo extends EffectEntity {
  alignment: string;
  style: string;
  hq_name: string;
  hq_desc: string;
  rank: string;
}

export interface RelationInfo {
  target_id: string;
  name: string;
  relation: string;
  realm: string;
  sect: string;
}

// --- 地图与区域 (Map & Region) ---

export type MapMatrix = string[][];

export interface RegionSummary extends EntityBase, Coordinates {
  type: string;
  sect_name?: string;
}

export interface RegionDetail extends EntityBase {
  desc: string;
  type: string;
  type_name: string; // 中文类型名
  
  essence?: { 
    type: string; 
    density: number; 
  };
  
  animals: EffectEntity[];
  plants: EffectEntity[];
}

// --- 天地灵机 ---

export interface CelestialPhenomenon {
  id: number;
  name: string;
  desc: string;
  rarity: string;
  duration_years?: number;
  effect_desc?: string;
}

// --- 事件 (Events) ---

export interface GameEvent {
  id: string;
  text: string;
  content?: string; // 详细描述
  year: number;
  month: number;
  // 排序权重
  timestamp: number; 
  relatedAvatarIds: string[];
  isMajor: boolean;
  isStory: boolean;
}

// --- 悬浮提示 (Hover) ---

export type HoverSegment = {
  text: string;
  color?: string;
};

export type HoverLine = HoverSegment[];
