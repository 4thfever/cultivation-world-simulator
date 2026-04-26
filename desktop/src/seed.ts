import fs from 'node:fs'

const ALLOWED_SEED_KEYS = new Set([
  'CWS_DEFAULT_LLM_BASE_URL',
  'CWS_DEFAULT_LLM_MODEL',
  'CWS_DEFAULT_LLM_FAST_MODEL',
  'CWS_DEFAULT_LLM_API_FORMAT',
  'CWS_DEFAULT_LLM_MODE',
  'CWS_DEFAULT_LLM_MAX_CONCURRENT_REQUESTS',
  'CWS_DEFAULT_LLM_API_KEY',
])

export function readSeedEnv(seedFile: string): NodeJS.ProcessEnv {
  if (!fs.existsSync(seedFile)) return {}

  const raw = fs.readFileSync(seedFile, 'utf-8')
  const parsed = JSON.parse(raw) as Record<string, unknown>
  const env: NodeJS.ProcessEnv = {}

  for (const [key, value] of Object.entries(parsed)) {
    if (!ALLOWED_SEED_KEYS.has(key)) continue
    if (typeof value !== 'string' || !value.trim()) continue
    env[key] = value
  }

  return env
}
