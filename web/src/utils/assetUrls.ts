export function withBasePublicPath(path: string): string {
  const normalizedPath = path.replace(/^\/+/, '')
  return `${import.meta.env.BASE_URL}${normalizedPath}`
}

export function getGameAssetUrl(path: string): string {
  const normalizedPath = path.replace(/^\/+/, '')
  return `/assets/${normalizedPath}`
}
