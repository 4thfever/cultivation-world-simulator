import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'

import { readSeedEnv } from './seed.js'

test('readSeedEnv returns empty env when seed file is missing', () => {
  assert.deepEqual(readSeedEnv(path.join(os.tmpdir(), 'missing-cws-seed.json')), {})
})

test('readSeedEnv only returns allowed non-empty llm seed keys', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cws-seed-'))
  const seedFile = path.join(dir, 'steam-seed.json')
  fs.writeFileSync(seedFile, JSON.stringify({
    CWS_DEFAULT_LLM_BASE_URL: 'https://api.example.test',
    CWS_DEFAULT_LLM_API_KEY: 'free-key',
    CWS_NO_BROWSER: '0',
    CWS_DEFAULT_LLM_MODEL: '',
  }))

  assert.deepEqual(readSeedEnv(seedFile), {
    CWS_DEFAULT_LLM_BASE_URL: 'https://api.example.test',
    CWS_DEFAULT_LLM_API_KEY: 'free-key',
  })
})
