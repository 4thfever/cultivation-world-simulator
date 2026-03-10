import { describe, it, expect } from 'vitest'
import {
  processNewEvents,
  mergeAndSortEvents,
  avatarIdToColor,
  buildAvatarColorMap,
  buildSectColorMap,
  tokenizeEventContent,
  escapeHtml,
  highlightAvatarNames,
  MAX_EVENTS,
  type AvatarColorInfo,
} from '@/utils/eventHelper'
import type { GameEvent } from '@/types/core'

describe('eventHelper', () => {
  describe('processNewEvents', () => {
    it('should return empty array for empty input', () => {
      expect(processNewEvents([], 100, 1)).toEqual([])
      expect(processNewEvents(null as any, 100, 1)).toEqual([])
    })

    it('should process raw events with default year/month', () => {
      const rawEvents = [
        { id: '1', text: 'Event 1' },
        { id: '2', text: 'Event 2' },
      ]

      const result = processNewEvents(rawEvents, 100, 5)

      expect(result).toHaveLength(2)
      expect(result[0]).toMatchObject({
        id: '1',
        text: 'Event 1',
        year: 100,
        month: 5,
        timestamp: 100 * 12 + 5,
        _seq: 0,
      })
      expect(result[1]._seq).toBe(1)
    })

    it('should use event year/month when provided', () => {
      const rawEvents = [{ id: '1', year: 50, month: 3 }]

      const result = processNewEvents(rawEvents, 100, 5)

      expect(result[0].year).toBe(50)
      expect(result[0].month).toBe(3)
      expect(result[0].timestamp).toBe(50 * 12 + 3)
    })
  })

  describe('mergeAndSortEvents', () => {
    const createEvent = (id: string, timestamp: number, createdAt?: number): GameEvent => ({
      id,
      timestamp,
      createdAt,
      year: Math.floor(timestamp / 12),
      month: timestamp % 12,
      text: `Event ${id}`,
      relatedAvatarIds: [],
    } as any) // Partial mock is enough for sorting logic

    it('should merge events without duplicates', () => {
      const existing = [createEvent('1', 100), createEvent('2', 101)]
      const newEvents = [createEvent('2', 101), createEvent('3', 102)]

      const result = mergeAndSortEvents(existing, newEvents)

      expect(result).toHaveLength(3)
      expect(result.map(e => e.id)).toEqual(['1', '2', '3'])
    })

    it('should sort by timestamp ascending', () => {
      const existing = [createEvent('3', 300)]
      const newEvents = [createEvent('1', 100), createEvent('2', 200)]

      const result = mergeAndSortEvents(existing, newEvents)

      expect(result.map(e => e.id)).toEqual(['1', '2', '3'])
    })

    it('should sort by createdAt when timestamps are equal', () => {
      const existing: GameEvent[] = []
      const newEvents = [
        createEvent('2', 100, 2000),
        createEvent('1', 100, 1000),
      ]

      const result = mergeAndSortEvents(existing, newEvents)

      expect(result.map(e => e.id)).toEqual(['1', '2'])
    })

    it('should truncate to MAX_EVENTS', () => {
      const events = Array.from({ length: MAX_EVENTS + 50 }, (_, i) =>
        createEvent(`${i}`, i)
      )

      const result = mergeAndSortEvents([], events)

      expect(result).toHaveLength(MAX_EVENTS)
      // Should keep the latest events.
      expect(result[0].id).toBe('50')
    })
  })

  describe('avatarIdToColor', () => {
    it('should return consistent color for same id', () => {
      const color1 = avatarIdToColor('avatar-123')
      const color2 = avatarIdToColor('avatar-123')
      expect(color1).toBe(color2)
    })

    it('should return different colors for different ids', () => {
      const color1 = avatarIdToColor('avatar-123')
      const color2 = avatarIdToColor('avatar-456')
      expect(color1).not.toBe(color2)
    })

    it('should return valid HSL color', () => {
      const color = avatarIdToColor('test-id')
      expect(color).toMatch(/^hsl\(\d+, 70%, 65%\)$/)
    })
  })

  describe('buildAvatarColorMap', () => {
    it('should build map from avatar list', () => {
      const avatars = [
        { id: '1', name: 'Alice' },
        { id: '2', name: 'Bob' },
      ]

      const map = buildAvatarColorMap(avatars)

      expect(map.size).toBe(2)
      expect(map.has('Alice')).toBe(true)
      expect(map.has('Bob')).toBe(true)
    })

    it('should skip avatars without name', () => {
      const avatars = [
        { id: '1', name: 'Alice' },
        { id: '2' },  // No name.
      ]

      const map = buildAvatarColorMap(avatars)

      expect(map.size).toBe(1)
    })
  })

  describe('buildSectColorMap', () => {
    it('should build map from sect regions with fixed colors', () => {
      const map = buildSectColorMap([
        { sect_id: 1, sect_name: 'Azure Sect', sect_color: '#4DD0E1' },
        { sect_id: 2, sect_name: 'Crimson Hall', sect_color: '#8D6E63' },
      ])

      expect(map.get('Azure Sect')).toEqual({ id: 1, color: '#4DD0E1' })
      expect(map.get('Crimson Hall')).toEqual({ id: 2, color: '#8D6E63' })
    })

    it('should skip invalid sect entries and apply default color', () => {
      const map = buildSectColorMap([
        { sect_name: 'No Id Sect', sect_color: '#111111' },
        { sect_id: 3, sect_color: '#222222' },
        { sect_id: 4, sect_name: 'No Color Sect' },
      ])

      expect(map.has('No Id Sect')).toBe(false)
      expect(map.get('No Color Sect')).toEqual({ id: 4, color: '#FFFFFF' })
    })
  })

  describe('highlightAvatarNames', () => {
    it('should escape html even when colorMap is empty', () => {
      const text = 'Hello World'
      const result = highlightAvatarNames(text, new Map())
      expect(result).toBe(text)
    })

    it('should highlight avatar names with color spans', () => {
      const colorMap = new Map<string, AvatarColorInfo>([
        ['Alice', { id: 'Alice', color: 'hsl(100, 70%, 65%)' }]
      ])
      const text = 'Alice defeated the enemy'

      const result = highlightAvatarNames(text, colorMap)

      expect(result).toContain('<span')
      expect(result).toContain('Alice')
      expect(result).toContain('hsl(100, 70%, 65%)')
    })

    it('should escape HTML in names', () => {
      const colorMap = new Map<string, AvatarColorInfo>([
        ['<script>', { id: 'script', color: 'hsl(0, 70%, 65%)' }]
      ])
      const text = 'User <script> logged in'

      const result = highlightAvatarNames(text, colorMap)

      expect(result).not.toContain('<script>')
      expect(result).toContain('&lt;script&gt;')
    })

    it('should match longer names first to avoid partial matches', () => {
      const colorMap = new Map<string, AvatarColorInfo>([
        ['张三', { id: 'zhangsan', color: 'hsl(100, 70%, 65%)' }],
        ['张三丰', { id: 'zhangsanfeng', color: 'hsl(200, 70%, 65%)' }],
      ])
      const text = '张三丰是一位大师'

      const result = highlightAvatarNames(text, colorMap)

      // Should match 张三丰, not 张三.
      expect(result).toContain('hsl(200, 70%, 65%)')
      // 张三 should not be separately highlighted within 张三丰.
      const matches = result.match(/hsl\(100/g)
      expect(matches).toBeNull()
    })

    it('should highlight multiple occurrences of the same name', () => {
      const colorMap = new Map<string, AvatarColorInfo>([
        ['张三丰', { id: 'zhangsanfeng', color: 'hsl(200, 70%, 65%)' }],
        ['李白', { id: 'libai', color: 'hsl(300, 70%, 65%)' }],
      ])
      const text = '张三丰和李白聊天，张三丰说了个笑话，李白笑了'

      const result = highlightAvatarNames(text, colorMap)

      // 张三丰 appears twice.
      const zhangMatches = result.match(/hsl\(200/g)
      expect(zhangMatches).toHaveLength(2)
      // 李白 appears twice.
      const liMatches = result.match(/hsl\(300/g)
      expect(liMatches).toHaveLength(2)
    })

    it('should handle both overlapping names appearing in text', () => {
      const colorMap = new Map<string, AvatarColorInfo>([
        ['张三', { id: 'zhangsan', color: 'hsl(100, 70%, 65%)' }],
        ['张三丰', { id: 'zhangsanfeng', color: 'hsl(200, 70%, 65%)' }],
      ])
      const text = '张三丰和张三是朋友'

      const result = highlightAvatarNames(text, colorMap)

      // 张三丰 should be highlighted with hsl(200).
      const zhangfengMatches = result.match(/hsl\(200/g)
      expect(zhangfengMatches).toHaveLength(1)
      // 张三 should be highlighted with hsl(100) exactly once (not inside 张三丰).
      const zhangsanMatches = result.match(/hsl\(100/g)
      expect(zhangsanMatches).toHaveLength(1)
    })

    it('should escape regex special characters in names', () => {
      const colorMap = new Map<string, AvatarColorInfo>([
        ['张三(test)', { id: 'zhangsan', color: 'hsl(100, 70%, 65%)' }],
        ['李白[1]', { id: 'libai', color: 'hsl(200, 70%, 65%)' }],
      ])
      const text = '张三(test)和李白[1]见面了'

      const result = highlightAvatarNames(text, colorMap)

      // Both names should be highlighted despite having regex special chars.
      expect(result).toContain('hsl(100, 70%, 65%)')
      expect(result).toContain('hsl(200, 70%, 65%)')
      expect(result).toContain('data-avatar-id="zhangsan"')
      expect(result).toContain('data-avatar-id="libai"')
    })
  })

  describe('tokenizeEventContent', () => {
    it('should preserve plain text when no avatar names match', () => {
      const text = '无人提及角色名'
      const tokens = tokenizeEventContent(
        text,
        new Map<string, AvatarColorInfo>([['Alice', { id: '1', color: 'hsl(1, 70%, 65%)' }]])
      )

      expect(tokens).toEqual([{ type: 'text', text }])
    })

    it('should split mixed text and avatar names into structured tokens', () => {
      const colorMap = new Map<string, AvatarColorInfo>([
        ['张三丰', { id: 'zhangsanfeng', color: 'hsl(200, 70%, 65%)' }],
        ['李白', { id: 'libai', color: 'hsl(300, 70%, 65%)' }],
      ])
      const tokens = tokenizeEventContent('张三丰与李白论道', colorMap)

      expect(tokens).toEqual([
        { type: 'avatar', text: '张三丰', avatarId: 'zhangsanfeng', color: 'hsl(200, 70%, 65%)' },
        { type: 'text', text: '与' },
        { type: 'avatar', text: '李白', avatarId: 'libai', color: 'hsl(300, 70%, 65%)' },
        { type: 'text', text: '论道' },
      ])
    })

    it('should tokenize sect names and keep avatar priority on duplicate names', () => {
      const avatarMap = new Map<string, AvatarColorInfo>([
        ['Azure Sect', { id: 'a1', color: 'hsl(100, 70%, 65%)' }],
      ])
      const sectMap = buildSectColorMap([
        { sect_id: 1, sect_name: 'Azure Sect', sect_color: '#4DD0E1' },
        { sect_id: 2, sect_name: 'Crimson Hall', sect_color: '#8D6E63' },
      ])

      const tokens = tokenizeEventContent('Azure Sect meets Crimson Hall', avatarMap, sectMap)

      expect(tokens).toEqual([
        { type: 'avatar', text: 'Azure Sect', avatarId: 'a1', color: 'hsl(100, 70%, 65%)' },
        { type: 'text', text: ' meets ' },
        { type: 'sect', text: 'Crimson Hall', sectId: 2, color: '#8D6E63' },
      ])
    })
  })

  describe('escapeHtml', () => {
    it('should escape dangerous html characters', () => {
      expect(escapeHtml('<img src=x onerror=alert(1)>')).toBe('&lt;img src=x onerror=alert(1)&gt;')
    })
  })
})
