/**
 * 字典映射与翻译工具
 */

const ELEMENT_MAP: Record<string, string> = {
  'metal': '金',
  'wood': '木',
  'water': '水',
  'fire': '火',
  'earth': '土',
  'none': '无',
  // Capitalized versions just in case
  'Metal': '金',
  'Wood': '木',
  'Water': '水',
  'Fire': '火',
  'Earth': '土',
  'None': '无'
};

export function translateElement(type: string): string {
  return ELEMENT_MAP[type] || type;
}

