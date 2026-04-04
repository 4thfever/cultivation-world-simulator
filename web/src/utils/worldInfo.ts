import worldInfoCsvText from '../../../static/game_configs/world_info.csv?raw'

export interface WorldInfoCsvRow {
  title: string
  titleId: string
  nameId: string
  descId: string
  fallbackDesc: string
}

export interface WorldInfoEntry {
  id: string
  title: string
  name: string
  desc: string
}

function parseCsvLine(line: string): string[] {
  const fields: string[] = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i]
    const next = line[i + 1]

    if (char === '"') {
      if (inQuotes && next === '"') {
        current += '"'
        i += 1
      } else {
        inQuotes = !inQuotes
      }
      continue
    }

    if (char === ',' && !inQuotes) {
      fields.push(current)
      current = ''
      continue
    }

    current += char
  }

  fields.push(current)
  return fields
}

export function parseWorldInfoCsv(csvText: string): WorldInfoCsvRow[] {
  const lines = csvText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)

  if (lines.length <= 2) {
    return []
  }

  return lines.slice(2).map((line) => {
    const [title = '', titleId = '', nameId = '', descId = '', fallbackDesc = ''] = parseCsvLine(line)
    return {
      title,
      titleId,
      nameId,
      descId,
      fallbackDesc,
    }
  })
}

const worldInfoRows = parseWorldInfoCsv(worldInfoCsvText)

export function loadWorldInfoRows(): WorldInfoCsvRow[] {
  return worldInfoRows
}

export function translateWorldInfoRows(
  rows: WorldInfoCsvRow[],
  t: (key: string) => string,
): WorldInfoEntry[] {
  return rows.map((row) => ({
    id: row.titleId,
    title: translateWorldInfoField(t, row.titleId, row.title),
    name: translateWorldInfoField(t, row.nameId, row.title),
    desc: translateWorldInfoField(t, row.descId, row.fallbackDesc),
  }))
}

function translateWorldInfoField(
  t: (key: string) => string,
  id: string,
  fallback: string,
): string {
  const key = `game.world_info.entries.${id}`
  const translated = t(key)
  return translated === key ? fallback : translated
}
