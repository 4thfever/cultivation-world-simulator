import type { GameEvent, HoverLine } from '../types/game'

let localEventIdCounter = 0

function nextLocalEventId(prefix: string) {
  localEventIdCounter += 1
  return `${prefix}-${Date.now()}-${localEventIdCounter}`
}

export function normalizeHoverLines(raw: unknown): HoverLine[] {
  if (!Array.isArray(raw)) return []
  return raw.map((line) => {
    if (!Array.isArray(line)) {
      return [{ text: line != null ? String(line) : '' }]
    }
    const segments = line.map((segment) => {
      if (segment && typeof segment === 'object') {
        const record = segment as Record<string, unknown>
        const textValue = 'text' in record ? record.text : ''
        const colorValue = 'color' in record ? record.color : undefined
        const text = textValue != null ? String(textValue) : ''
        const color = typeof colorValue === 'string' && colorValue ? colorValue : undefined
        return { text, color }
      }
      return { text: segment != null ? String(segment) : '' }
    })
    return segments.length ? segments : [{ text: '' }]
  })
}

export function normalizeGameEvent(raw: unknown): GameEvent | null {
  if (raw == null) {
    return null
  }

  if (typeof raw === 'string') {
    return {
      id: nextLocalEventId('legacy'),
      text: raw,
      relatedAvatarIds: []
    }
  }

  if (typeof raw === 'object') {
    const record = raw as Record<string, unknown>
    const textSource = record.text ?? record.content ?? ''
    const text = typeof textSource === 'string' ? textSource : String(textSource ?? '')
    const idSource = record.id
    const id = typeof idSource === 'string' && idSource ? idSource : nextLocalEventId('evt')
    const relatedSource = record.related_avatar_ids ?? record.relatedAvatarIds ?? []
    const relatedAvatarIds = Array.isArray(relatedSource) ? relatedSource.map((val) => String(val)) : []
    const content = typeof record.content === 'string' ? record.content : undefined
    const year = typeof record.year === 'number' ? record.year : undefined
    const month = typeof record.month === 'number' ? record.month : undefined
    const monthStampRaw = record.month_stamp ?? record.monthStamp
    const monthStamp = typeof monthStampRaw === 'number' ? monthStampRaw : undefined
    const isMajor = Boolean(record.is_major ?? record.isMajor ?? false)
    const isStory = Boolean(record.is_story ?? record.isStory ?? false)

    return {
      id,
      text: text || content || '',
      content,
      year,
      month,
      monthStamp,
      relatedAvatarIds,
      isMajor,
      isStory
    }
  }

  return {
    id: nextLocalEventId('legacy'),
    text: String(raw),
    relatedAvatarIds: []
  }
}
