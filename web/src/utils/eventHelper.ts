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
    createdAt: e.created_at,
    _seq: index 
  }));
}

/**
 * 合并并排序事件列表
 * 1. 优先使用 createdAt (精确时间戳) 升序
 * 2. 其次按月时间戳升序
 * 3. 最后按序列号升序
 * 4. 保留最新的 MAX_EVENTS 条
 */
export function mergeAndSortEvents(existingEvents: GameEvent[], newEvents: GameEvent[]): GameEvent[] {
  // 合并
  const combined = [...existingEvents]; // Copy existing
  // Add new ones only if not exists (by id)
  const existingIds = new Set(existingEvents.map(e => e.id));
  for (const ev of newEvents) {
      if (!existingIds.has(ev.id)) {
          combined.push(ev);
      }
  }
  
  combined.sort((a, b) => {
    // 0. 如果都有 createdAt，优先比较
    // 注意：SQLite 可能没有返回历史数据的 createdAt，或者为 0
    if (a.createdAt && b.createdAt && a.createdAt > 0 && b.createdAt > 0) {
        // float comparison
        return a.createdAt - b.createdAt;
    }

    // 1. 先按时间戳升序（最旧的月在上面）
    const ta = a.timestamp;
    const tb = b.timestamp;
    if (tb !== ta) {
      return ta - tb;
    }
    
    // 2. 时间相同时，按原始逻辑顺序升序（先发生的在上面）
    // 如果其中一个有 createdAt 而另一个没有（不太可能，除非混合了旧数据）
    // 假设 tick 数据有 createdAt，API 数据也有。
    
    // 如果没有 createdAt，回退到 _seq
    const seqA = a._seq ?? -1;
    const seqB = b._seq ?? -1;
    
    if (seqA === -1 && seqB === -1) return 0;
    
    return seqA - seqB;
  });
  
  // 保留最新的 N 条
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

export interface AvatarColorInfo {
  id: string;
  color: string;
}

/**
 * 根据角色列表构建 name -> { id, color } 映射表。
 */
export function buildAvatarColorMap(
  avatars: Array<{ id: string; name?: string }>
): Map<string, AvatarColorInfo> {
  const map = new Map<string, AvatarColorInfo>();
  for (const av of avatars) {
    if (av.name) {
      map.set(av.name, { id: av.id, color: avatarIdToColor(av.id) });
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
 * 生成的 span 带有 data-avatar-id 属性，可用于点击跳转。
 */
export function highlightAvatarNames(
  text: string,
  colorMap: Map<string, AvatarColorInfo>
): string {
  if (!text || colorMap.size === 0) return text;

  // 按名字长度倒序排列，避免部分匹配（如 "张三" 匹配到 "张三丰"）。
  const names = [...colorMap.keys()].sort((a, b) => b.length - a.length);

  let result = text;
  for (const name of names) {
    const info = colorMap.get(name)!;
    const escaped = name.replace(/[&<>"']/g, c => HTML_ESCAPE_MAP[c] || c);
    result = result.replaceAll(
      name,
      `<span class="clickable-avatar" data-avatar-id="${info.id}" style="color:${info.color};cursor:pointer">${escaped}</span>`
    );
  }
  return result;
}

