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
  type_name?: string; // 新增：中文类型名，如"丹药"、"破境"等
  color?: string | number[]; // 某些实体自带颜色
  drops?: EffectEntity[];
  hq_name?: string;
  hq_desc?: string;
}

export interface Material extends EffectEntity {
  count: number;
}

// --- 角色 (Avatar) ---

export interface AvatarSummary extends EntityBase, Coordinates {
  action?: string;
  action_emoji?: string;
  gender?: string;
  pic_id?: number;
  is_dead?: boolean;
}

export interface AvatarDetail extends EntityBase {
  // 基础信息
  gender: string;
  age: number;
  origin: string;
  lifespan: number;
  nickname?: string;
  appearance: string; // 外貌描述
  is_dead?: boolean;
  action_state?: string; // 当前正在进行的动作描述
  death_info?: {
    time: number;
    reason: string;
    location: [number, number];
  };
  
  // 修行状态
  realm: string;
  level: number;
  hp: { cur: number; max: number };
  magic_stone: number;
  base_battle_strength: number;
  
  // 情绪
  emotion: {
    name: string;
    emoji: string;
    desc: string;
  };
  
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
  orthodoxy?: EffectEntity; // 新增道统字段
  personas: EffectEntity[];
  technique?: EffectEntity;
  weapon?: EffectEntity & { proficiency: string };
  auxiliary?: EffectEntity;
  spirit_animal?: EffectEntity;
  
  // 列表数据
  materials: Material[];
  relations: RelationInfo[];
  
  // 附加信息
  "当前效果"?: string;
}

export interface SectInfo extends EffectEntity {
  alignment: string;
  style: string;
  hq_name: string;
  hq_desc: string;
  rank: string;
}

export interface SectMember {
  id: string;
  name: string;
  pic_id: number;
  gender: string;
  rank: string;
  realm: string;
}

export interface SectDetail extends EntityBase {
  desc: string;
  alignment: string;
  style: string;
  hq_name: string;
  hq_desc: string;
  effect_desc: string;
  technique_names?: string[]; // Deprecated
  techniques: EffectEntity[];
  preferred_weapon: string;
  members: SectMember[];
  orthodoxy: EffectEntity;
}

export interface RelationInfo {
  target_id: string;
  name: string;
  relation: string;
  relation_type: string;
  realm: string;
  sect: string;
  is_mortal?: boolean;
  label_key?: string;
  target_gender?: string;
}

// --- 地图与区域 (Map & Region) ---

export type MapMatrix = string[][];

export interface RegionSummary extends EntityBase, Coordinates {
  type: string;
  sect_id?: number;
  sub_type?: string; // for cultivate regions: "cave" or "ruin"
}

export interface RegionDetail extends EntityBase {
  desc: string;
  type: string;
  type_name: string; // 中文类型名
  sect_id?: number;
  
  essence?: { 
    type: string; 
    density: number; 
  };
  
  // 洞府主人（修炼区域特有）
  host?: {
    id: string;
    name: string;
  } | null;
  
  animals: EffectEntity[];
  plants: EffectEntity[];
  lodes: EffectEntity[];
  store_items?: (EffectEntity & { price: number })[];
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

// web/src/types/core.ts

// 新增秘境信息接口
export interface HiddenDomainInfo {
  id: string;
  name: string;
  desc: string;
  required_realm: string; // 限制境界
  danger_prob: number; // 凶险度 (0.0 - 1.0)
  drop_prob: number;   // 机缘度 (0.0 - 1.0)
  is_open: boolean;    // 是否开启
  cd_years: number;    // CD 年份
  open_prob: number;   // 开启概率
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
  
  // 真实创建时间 (用于精确排序)
  createdAt?: number;

  // 运行时辅助字段
  _seq?: number; 
}
