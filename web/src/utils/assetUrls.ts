export function withBasePublicPath(path: string): string {
  const normalizedPath = path.replace(/^\/+/, '')
  return `${import.meta.env.BASE_URL}${normalizedPath}`
}

const GAME_ASSET_BASE = '/assets'

export function getGameAssetUrl(path: string): string {
  const normalizedPath = path.replace(/^\/+/, '')
  return `${GAME_ASSET_BASE}/${normalizedPath}`
}

export function getAvatarPortraitUrl(gender: string | undefined, picId: number | null | undefined): string {
  if (!picId) return ''
  const normalizedGender = String(gender || '').toLowerCase()
  const dir = normalizedGender === 'female' || normalizedGender === '女' ? 'females' : 'males'
  return getGameAssetUrl(`${dir}/${picId}.png`)
}
