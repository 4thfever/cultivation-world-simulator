import type { EventDTO } from '@/types/api';
import type { GameEvent } from '../types/core';

export const MAX_EVENTS = 300;

/**
 * 处理新事件列表，转换为 Domain 对象并分配序列号
 */
export function processNewEvents(rawEvents: EventDTO[], currentYear: number, currentMonth: number): GameEvent[] {
  if (!rawEvents || rawEvents.length === 0) return [];

  return rawEvents.map((e, index) => ({
    id: e.id,
    text: e.text,
    content: e.content,
    year: e.year ?? currentYear,
    month: e.month ?? currentMonth,
    timestamp: (e.year ?? currentYear) * 12 + (e.month ?? currentMonth),
    relatedAvatarIds: e.related_avatar_ids || [],
    relatedSects: e.related_sects,
    isMajor: e.is_major,
    isStory: e.is_story,
    renderKey: e.render_key,
    renderParams: e.render_params,
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

export interface SectColorInfo {
  id: number;
  color: string;
}

export interface EventContentToken {
  type: 'text' | 'avatar' | 'sect';
  text: string;
  avatarId?: string;
  sectId?: number;
  color?: string;
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

/**
 * 根据宗门列表构建 name -> { id, color } 映射。
 * 颜色来自后端透传的 sect.csv color，缺省时使用白色。
 */
export function buildSectColorMap(
  sects: Array<{ sect_id?: number; sect_name?: string; sect_color?: string }>
): Map<string, SectColorInfo> {
  const map = new Map<string, SectColorInfo>();
  for (const sect of sects) {
    const id = sect.sect_id;
    const name = sect.sect_name;
    if (id == null || !name) continue;
    map.set(name, { id, color: sect.sect_color || '#FFFFFF' });
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

export function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, c => HTML_ESCAPE_MAP[c] || c);
}

/**
 * 将事件文本拆分为安全渲染 token，避免在组件里使用 v-html。
 */
export function tokenizeEventContent(
  text: string,
  colorMap: Map<string, AvatarColorInfo>,
  sectColorMap: Map<string, SectColorInfo> = new Map()
): EventContentToken[] {
  if (!text) return [];
  const entityByName = new Map<string, { type: 'avatar' | 'sect'; id: string | number; color: string }>();
  for (const [name, info] of colorMap.entries()) {
    entityByName.set(name, { type: 'avatar', id: info.id, color: info.color });
  }
  // 同名冲突时保留角色优先级，避免破坏原有行为。
  for (const [name, info] of sectColorMap.entries()) {
    if (!entityByName.has(name)) {
      entityByName.set(name, { type: 'sect', id: info.id, color: info.color });
    }
  }

  if (entityByName.size === 0) {
    return [{ type: 'text', text }];
  }

  const names = [...entityByName.keys()].sort((a, b) => b.length - a.length);
  const escapeRegex = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const pattern = new RegExp(names.map(escapeRegex).join('|'), 'g');

  const tokens: EventContentToken[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    const start = match.index;
    const matchedText = match[0];

    if (start > lastIndex) {
      tokens.push({
        type: 'text',
        text: text.slice(lastIndex, start),
      });
    }

    const info = entityByName.get(matchedText);
    if (info?.type === 'avatar') {
      tokens.push({
        type: 'avatar',
        text: matchedText,
        avatarId: String(info.id),
        color: info.color,
      });
    } else if (info?.type === 'sect') {
      tokens.push({
        type: 'sect',
        text: matchedText,
        sectId: Number(info.id),
        color: info.color,
      });
    } else {
      // 理论上不会走到这里；保底退化为普通文本，避免渲染异常。
      tokens.push({
        type: 'text',
        text: matchedText,
      });
    }

    lastIndex = start + matchedText.length;
  }

  if (lastIndex < text.length) {
    tokens.push({
      type: 'text',
      text: text.slice(lastIndex),
    });
  }

  return tokens;
}

/**
 * 高亮文本中的角色名，返回 HTML 字符串。
 * 生成的 span 带有 data-avatar-id 属性，可用于点击跳转。
 *
 * 实现说明：
 * - 使用单次正则替换（而非多次 replaceAll），避免重叠名字问题。
 * - 例如 "张三" 和 "张三丰"，多次 replaceAll 会导致 "张三丰" 中的 "张三" 被错误匹配。
 * - 单次正则 /(张三丰|张三)/g 配合长名字优先排序，正则引擎匹配 "张三丰" 后会跳过这3个字符，
 *   不会再回头匹配 "张三"。
 * - /g flag 确保所有出现都被替换（一次扫描，callback 被调用多次）。
 */
export function highlightAvatarNames(
  text: string,
  colorMap: Map<string, AvatarColorInfo>
): string {
  if (!text) return text;

  return tokenizeEventContent(text, colorMap)
    .map((token) => {
      if (token.type === 'avatar') {
        return `<span class="clickable-avatar" data-avatar-id="${token.avatarId}" style="color:${token.color};cursor:pointer">${escapeHtml(token.text)}</span>`;
      }
      return escapeHtml(token.text);
    })
    .join('');
}

