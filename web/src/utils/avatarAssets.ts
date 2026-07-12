export type AvatarAssetLibrary = { male: number[]; female: number[] }

export type AvatarAssetLibraries = {
  [raceId: string]: AvatarAssetLibrary | undefined
  human: AvatarAssetLibrary
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
    return { human: { male: [], female: [] } }
  }

  const record = source as Record<string, unknown>
  const normalized: AvatarAssetLibraries = { human: { male: [], female: [] } }
  for (const [raceId, library] of Object.entries(record)) {
    if (library && typeof library === 'object' && !Array.isArray(library)) {
      normalized[raceId] = toLibrary(library)
    }
  }

  normalized.human = normalized.human || { male: [], female: [] }
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
  const library = candidate || libraries.human || { male: [], female: [] }
  return library[genderKey] || []
}
