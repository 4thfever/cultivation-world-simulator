export interface WaitForHealthOptions {
  url: string
  timeoutMs?: number
  intervalMs?: number
  fetchImpl?: typeof fetch
  now?: () => number
  delay?: (ms: number) => Promise<void>
}

export async function waitForHealth(options: WaitForHealthOptions): Promise<void> {
  const timeoutMs = options.timeoutMs ?? 30000
  const intervalMs = options.intervalMs ?? 500
  const fetchImpl = options.fetchImpl ?? fetch
  const now = options.now ?? (() => Date.now())
  const delay = options.delay ?? ((ms) => new Promise<void>((resolve) => setTimeout(resolve, ms)))
  const deadline = now() + timeoutMs
  let lastError: unknown

  while (now() <= deadline) {
    try {
      const response = await fetchImpl(options.url)
      if (response.ok) return
      lastError = new Error(`Health check returned HTTP ${response.status}`)
    } catch (error) {
      lastError = error
    }

    await delay(intervalMs)
  }

  const message = lastError instanceof Error ? lastError.message : String(lastError ?? 'unknown error')
  throw new Error(`Backend health check timed out: ${message}`)
}
