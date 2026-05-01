const EXTERNAL_PROTOCOLS = new Set(['http:', 'https:'])

export function isAllowedAppNavigation(targetUrl: string, navigationUrl: string): boolean {
  try {
    return new URL(navigationUrl).origin === new URL(targetUrl).origin
  } catch {
    return false
  }
}

export function shouldOpenExternally(targetUrl: string, navigationUrl: string): boolean {
  try {
    const url = new URL(navigationUrl)
    return EXTERNAL_PROTOCOLS.has(url.protocol) && !isAllowedAppNavigation(targetUrl, navigationUrl)
  } catch {
    return false
  }
}
