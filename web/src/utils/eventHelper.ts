import type { GameEvent } from '../types/core';

export const MAX_EVENTS = 300;

/**
 * 处理新事件列表，转换为 Domain 对象并分配序列号
 */
export function processNewEvents(rawEvents: any[], currentYear: number, currentMonth: number): GameEvent[] {
  if (!rawEvents || rawEvents.length === 0) return [];

  return rawEvents.map((e, index) => ({
    id: e.id,
    text: e.text,
    content: e.content,
    year: e.year ?? currentYear,
    month: e.month ?? currentMonth,
    timestamp: (e.year ?? currentYear) * 12 + (e.month ?? currentMonth),
    relatedAvatarIds: e.related_avatar_ids || [],
    isMajor: e.is_major,
    isStory: e.is_story,
    _seq: index 
  }));
}

/**
 * 合并并排序事件列表
 * 1. 按时间戳升序
 * 2. 时间戳相同时，按序列号升序
 * 3. 保留最新的 MAX_EVENTS 条
 */
export function mergeAndSortEvents(existingEvents: GameEvent[], newEvents: GameEvent[]): GameEvent[] {
  const combined = [...newEvents, ...existingEvents];
  
  combined.sort((a, b) => {
    // 1. 先按时间戳升序（最旧的月在上面）
    const ta = a.timestamp;
    const tb = b.timestamp;
    if (tb !== ta) {
      return ta - tb;
    }
    
    // 2. 时间相同时，按原始逻辑顺序升序（先发生的在上面）
    // 旧事件通常没有 _seq (undefined)，视为最旧 (-1)
    const seqA = a._seq ?? -1;
    const seqB = b._seq ?? -1;
    
    // 如果都是旧事件，保持相对顺序 (Stable)
    if (seqA === -1 && seqB === -1) return 0;
    
    return seqA - seqB;
  });
  
  // 保留最新的 N 条 (因为是升序，最新的在最后，所以取最后 N 条)
  if (combined.length > MAX_EVENTS) {
    return combined.slice(-MAX_EVENTS);
  }
  
  return combined;
}

/**
 * 根据角色 ID 哈希生成一致的 HSL 颜色。
 */
export function avatarIdToColor(id: string): string {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = ((hash << 5) - hash) + id.charCodeAt(i);
    hash |= 0;
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 70%, 65%)`;
}

/**
 * 根据角色列表构建 name -> color 映射表。
 */
export function buildAvatarColorMap(
  avatars: Array<{ id: string; name?: string }>
): Map<string, string> {
  const map = new Map<string, string>();
  for (const av of avatars) {
    if (av.name) {
      map.set(av.name, avatarIdToColor(av.id));
    }
  }
  return map;
}

const HTML_ESCAPE_MAP: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
};

/**
 * 高亮文本中的角色名，返回 HTML 字符串。
 */
export function highlightAvatarNames(
  text: string,
  colorMap: Map<string, string>
): string {
  if (!text || colorMap.size === 0) return text;

  // 按名字长度倒序排列，避免部分匹配（如 "张三" 匹配到 "张三丰"）。
  const names = [...colorMap.keys()].sort((a, b) => b.length - a.length);

  let result = text;
  for (const name of names) {
    const color = colorMap.get(name)!;
    const escaped = name.replace(/[&<>"']/g, c => HTML_ESCAPE_MAP[c] || c);
    result = result.replaceAll(name, `<span style="color:${color}">${escaped}</span>`);
  }
  return result;
}

