import assert from 'node:assert/strict'
import type { ChildProcess } from 'node:child_process'
import test from 'node:test'

import { buildBackendEnv, collectSeedEnv, stopBackend } from './backend.js'

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

test('stopBackend kills the Windows backend process tree', () => {
  const taskkillPids: number[] = []
  const processRef = {
    pid: 4242,
    killed: false,
    kill: () => {
      throw new Error('Windows cleanup must use taskkill instead of SIGTERM')
    },
  } as unknown as ChildProcess

  const stopped = stopBackend(processRef, {
    platform: 'win32',
    taskkillRunner: (pid) => {
      taskkillPids.push(pid)
    },
  })

  assert.equal(stopped, true)
  assert.deepEqual(taskkillPids, [4242])
})

test('stopBackend sends SIGTERM on non-Windows platforms', () => {
  const signals: string[] = []
  const processRef = {
    pid: 4243,
    killed: false,
    kill: (signal: string) => {
      signals.push(signal)
      return true
    },
  } as unknown as ChildProcess

  const stopped = stopBackend(processRef, { platform: 'linux' })

  assert.equal(stopped, true)
  assert.deepEqual(signals, ['SIGTERM'])
})

test('stopBackend is a no-op for missing or already-killed processes', () => {
  const killedProcess = {
    killed: true,
    kill: () => {
      throw new Error('Already-killed process must not be killed again')
    },
  } as unknown as ChildProcess

  assert.equal(stopBackend(undefined), false)
  assert.equal(stopBackend(killedProcess), false)
})
