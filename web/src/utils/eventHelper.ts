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

