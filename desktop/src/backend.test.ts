import assert from 'node:assert/strict'
import test from 'node:test'

import { buildBackendEnv, collectSeedEnv } from './backend.js'

test('buildBackendEnv sets backend host, port, browser, shutdown and utf8 env', () => {
  const env = buildBackendEnv({
    port: 8123,
    baseEnv: {
      EXISTING: 'yes',
    },
  })

  assert.equal(env.EXISTING, 'yes')
  assert.equal(env.SERVER_HOST, '127.0.0.1')
  assert.equal(env.SERVER_PORT, '8123')
  assert.equal(env.CWS_NO_BROWSER, '1')
  assert.equal(env.CWS_DISABLE_AUTO_SHUTDOWN, '1')
  assert.equal(env.PYTHONUTF8, '1')
  assert.equal(env.PYTHONIOENCODING, 'utf-8')
})

test('buildBackendEnv preserves explicit utf8 overrides', () => {
  const env = buildBackendEnv({
    port: 8124,
    baseEnv: {
      PYTHONUTF8: '0',
      PYTHONIOENCODING: 'utf-8:replace',
    },
  })

  assert.equal(env.PYTHONUTF8, '0')
  assert.equal(env.PYTHONIOENCODING, 'utf-8:replace')
})

test('collectSeedEnv only forwards CWS_DEFAULT_LLM variables', () => {
  const env = collectSeedEnv({
    CWS_DEFAULT_LLM_BASE_URL: 'https://example.test',
    CWS_DEFAULT_LLM_API_KEY: 'free-key',
    CWS_NO_BROWSER: '0',
  })

  assert.deepEqual(env, {
    CWS_DEFAULT_LLM_BASE_URL: 'https://example.test',
    CWS_DEFAULT_LLM_API_KEY: 'free-key',
  })
})
