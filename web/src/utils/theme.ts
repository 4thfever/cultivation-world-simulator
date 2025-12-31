/**
 * 主题与样式工具
 * 集中管理颜色映射、稀有度判断等逻辑
 */

import type { EffectEntity } from '../types/core';

// 稀有度颜色映射
export const GRADE_COLORS: Record<string, string> = {
  '上品': '#c488fd', // Purple
  '宝物': '#c488fd',
  'SR': '#c488fd',
  'Upper': '#c488fd',
  
  '中品': '#88fdc4', // Green-ish
  'R': '#88fdc4',
  'Middle': '#88fdc4',
  
  '法宝': '#fddc88', // Gold
  'SSR': '#fddc88',
  'Artifact': '#fddc88',
  
  'Default': '#cccccc',

  // 境界映射
  '练气': '#cccccc', // White/Gray
  '筑基': '#88fdc4', // Green
  '金丹': '#c488fd', // Purple
  '元婴': '#fddc88', // Gold
};

/**
 * 获取实体的显示颜色
 * 优先使用实体自带的 color 属性，其次根据 grade/rarity 查找
 */
export function getEntityColor(entity: Partial<EffectEntity> | undefined | null): string | undefined {
  if (!entity) return undefined;

  // 1. 直接颜色属性 (RGB数组)
  if (entity.color && Array.isArray(entity.color) && entity.color.length === 3) {
    const [r, g, b] = entity.color;
    return `rgb(${r},${g},${b})`;
  }
  
  // 2. 直接颜色属性 (字符串)
  if (typeof entity.color === 'string') {
    return entity.color;
  }

  // 3. 根据稀有度/品级映射
  const grade = entity.grade || entity.rarity;
  if (!grade) return undefined;
  
  // 简单的包含匹配
  for (const [key, color] of Object.entries(GRADE_COLORS)) {
    if (grade.includes(key)) return color;
  }

  return undefined;
}

