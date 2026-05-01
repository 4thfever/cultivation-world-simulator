import { expect, test, type Page } from '@playwright/test'

const mockApi = process.env.CWS_SMOKE_MOCK_API === '1'
const allowConsolePatterns = [
  /Failed to load resource: net::ERR_FAILED/,
  /favicon/i,
]

const mockSettings = {
  schema_version: 1,
  ui: {
    locale: 'zh-CN',
    audio: {
      bgm_volume: 0,
      sfx_volume: 0,
    },
  },
  simulation: {
    auto_save_enabled: false,
    max_auto_saves: 5,
  },
  llm: {
    profile: {
      base_url: '',
      model_name: '',
      fast_model_name: '',
      mode: 'default',
      max_concurrent_requests: 4,
      has_api_key: false,
      api_format: 'openai',
    },
  },
  new_game_defaults: {
    content_locale: 'zh-CN',
    init_npc_num: 9,
    sect_num: 3,
    npc_awakening_rate_per_month: 0.01,
    world_lore: '',
  },
}

const mockRuntimeStatus = {
  ok: true,
  data: {
    status: 'idle',
    phase: 0,
    phase_name: 'idle',
    progress: 0,
    elapsed_seconds: 0,
    error: null,
    version: 'smoke',
    llm_check_failed: false,
    llm_error_message: '',
    is_paused: false,
    pause_reason: null,
    roleplay: null,
  },
}

async function installApiMocks(page: Page) {
  if (!mockApi) return

  await page.route('**/assets/splash.png', async (route) => {
    await route.fulfill({
      status: 204,
      contentType: 'image/png',
      body: '',
    })
  })

  await page.route('**/assets/splash.mp4', async (route) => {
    await route.fulfill({
      status: 204,
      contentType: 'video/mp4',
      body: '',
    })
  })

  await page.route('**/api/settings', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockSettings),
    })
  })

  await page.route('**/api/v1/query/runtime/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockRuntimeStatus),
    })
  })
}

test('production build renders the first screen without browser errors', async ({ page }) => {
  const consoleErrors: string[] = []
  const pageErrors: string[] = []

  page.on('console', (message) => {
    if (message.type() !== 'error') return
    const text = message.text()
    if (allowConsolePatterns.some((pattern) => pattern.test(text))) return
    consoleErrors.push(text)
  })
  page.on('pageerror', (error) => {
    pageErrors.push(error.message)
  })

  await installApiMocks(page)
  await page.goto('/', { waitUntil: 'networkidle' })

  const app = page.locator('#app')
  await expect(app).toBeAttached()
  await expect(app).not.toBeEmpty()
  await expect(page.locator('.splash-container, .app-layout, .loading-overlay').first()).toBeVisible()

  if (!mockApi) {
    const status = await page.request.get('/api/v1/query/runtime/status')
    expect(status.ok()).toBeTruthy()
  }

  expect(pageErrors).toEqual([])
  expect(consoleErrors).toEqual([])
})
