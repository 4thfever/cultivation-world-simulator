export function withBasePublicPath(path: string): string {
  const normalizedPath = path.replace(/^\/+/, '')
  return `${import.meta.env.BASE_URL}${normalizedPath}`
}

const GAME_ASSET_BASE = '/assets'

export function getGameAssetUrl(path: string): string {
  const normalizedPath = path.replace(/^\/+/, '')
  return `${GAME_ASSET_BASE}/${normalizedPath}`
}

export function getRealmAssetSlug(realm: string | null | undefined): string {
  const normalized = String(realm || '').trim().toLowerCase()
  const normalizedCompact = normalized.replace(/[\s-]+/g, '_')
  const mapping: Record<string, string> = {
    qi_refinement: 'qi_refining',
    qi_refining: 'qi_refining',
    foundation_establishment: 'foundation',
    foundation: 'foundation',
    core_formation: 'golden_core',
    golden_core: 'golden_core',
    nascent_soul: 'nascent_soul',
    '练气': 'qi_refining',
    '筑基': 'foundation',
    '金丹': 'golden_core',
    '元婴': 'nascent_soul',
  }
  return mapping[normalizedCompact] || 'qi_refining'
}

export function getAvatarIndexSlug(picId: number | null | undefined): string {
  return String(picId || 1).padStart(3, '0')
}

export function getYaoAvatarIndexSlug(picId: number | null | undefined): string {
  return String(picId || 1).padStart(2, '0')
}

export function getAvatarPortraitUrl(
  gender: string | undefined,
  picId: number | null | undefined,
  realm?: string | null,
  race?: string | null,
): string {
  if (!picId) return ''
  const normalizedGender = String(gender || '').toLowerCase()
  const dir = normalizedGender === 'female' || normalizedGender === '女' ? 'female' : 'male'
  const normalizedRace = String(race || 'human').trim().toLowerCase() || 'human'
  const root = normalizedRace === 'human' ? 'avatars' : `yao/${normalizedRace}`
  const indexSlug = normalizedRace === 'human' ? getAvatarIndexSlug(picId) : getYaoAvatarIndexSlug(picId)
  return getGameAssetUrl(`${root}/${dir}/${indexSlug}/${getRealmAssetSlug(realm)}.png`)
}
