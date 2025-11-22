/**
 * API 数据传输对象 (Data Transfer Objects)
 * 这些类型严格对应后端接口返回的 JSON 结构。
 */

import type { MapMatrix } from './core';

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
  events?: unknown[];
}

export interface TickPayloadDTO {
  type: 'tick';
  year: number;
  month: number;
  avatars?: Array<Partial<InitialStateDTO['avatars'] extends (infer U)[] ? U : never>>;
  events?: unknown[];
}

export interface MapResponseDTO {
  data: MapMatrix;
  regions: Array<{
    id: string | number;
    name: string;
    x: number;
    y: number;
    type: string;
    sect_name?: string;
  }>;
}

export interface HoverResponseDTO {
  lines: unknown; // 后端返回的可能是复杂的嵌套数组
}

// 详情接口返回的结构比较动态，通常包含 entity 的所有字段
export type DetailResponseDTO = Record<string, any>;

export interface SaveFileDTO {
  filename: string;
  save_time: string;
  game_time: string;
  version: string;
}

