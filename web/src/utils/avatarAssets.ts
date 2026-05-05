export type AvatarAssetLibrary = { male: number[]; female: number[] }

export type AvatarAssetLibraries = {
  [raceId: string]: AvatarAssetLibrary | number[] | undefined
  human: AvatarAssetLibrary
  males?: number[]
  females?: number[]
}

function toNumberList(value: unknown): number[] {
  if (!Array.isArray(value)) return []
  return value
    .map(item => Number(item))
    .filter(item => Number.isFinite(item) && item > 0)
}

function toLibrary(value: unknown): AvatarAssetLibrary {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return { male: [], female: [] }
  }
  const record = value as Record<string, unknown>
  return {
    male: toNumberList(record.male),
    female: toNumberList(record.female),
  }
}

export function normalizeAvatarAssetLibraries(raw: unknown): AvatarAssetLibraries {
  const source = (
    raw &&
    typeof raw === 'object' &&
    !Array.isArray(raw) &&
    'data' in raw &&
    (raw as { data?: unknown }).data &&
    typeof (raw as { data?: unknown }).data === 'object'
  )
    ? (raw as { data: unknown }).data
    : raw

  if (!source || typeof source !== 'object' || Array.isArray(source)) {
    return { human: { male: [], female: [] }, males: [], females: [] }
  }

  const record = source as Record<string, unknown>
  const hasRaceLibraries = Object.values(record).some(
    value => value && typeof value === 'object' && !Array.isArray(value) && ('male' in value || 'female' in value),
  )

  const normalized: AvatarAssetLibraries = { human: { male: [], female: [] } }
  if (hasRaceLibraries) {
    for (const [raceId, library] of Object.entries(record)) {
      if (raceId === 'males' || raceId === 'females') continue
      normalized[raceId] = toLibrary(library)
    }
  } else {
    normalized.human = {
      male: toNumberList(record.males),
      female: toNumberList(record.females),
    }
  }

  normalized.human = normalized.human || { male: [], female: [] }
  normalized.males = normalized.human.male
  normalized.females = normalized.human.female
  return normalized
}

export function getAvatarAssetIds(
  libraries: AvatarAssetLibraries | null | undefined,
  race: string | null | undefined,
  gender: string | null | undefined,
): number[] {
  if (!libraries) return []
  const normalizedGender = String(gender || '').toLowerCase()
  const genderKey = normalizedGender === 'female' || normalizedGender === '女' ? 'female' : 'male'
  const raceKey = String(race || 'human').trim().toLowerCase() || 'human'
  const candidate = libraries[raceKey]
  const library = (
    candidate && !Array.isArray(candidate) && 'male' in candidate
      ? candidate
      : libraries.human
  ) || { male: [], female: [] }
  return library[genderKey] || []
}
