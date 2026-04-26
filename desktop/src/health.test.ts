import assert from 'node:assert/strict'
import test from 'node:test'

import { waitForHealth } from './health.js'

test('waitForHealth returns after first ok response', async () => {
  let calls = 0
  await waitForHealth({
    url: 'http://127.0.0.1:8002/api/health',
    fetchImpl: async () => {
      calls += 1
      return new Response('{}', { status: 200 })
    },
    delay: async () => {},
  })

  assert.equal(calls, 1)
})

test('waitForHealth retries until ok response', async () => {
  let calls = 0
  let currentTime = 0

  await waitForHealth({
    url: 'http://127.0.0.1:8002/api/health',
    now: () => currentTime,
    timeoutMs: 1000,
    intervalMs: 100,
    fetchImpl: async () => {
      calls += 1
      currentTime += 100
      return new Response('{}', { status: calls >= 3 ? 200 : 503 })
    },
    delay: async () => {},
  })

  assert.equal(calls, 3)
})

test('waitForHealth throws on timeout', async () => {
  let currentTime = 0

  await assert.rejects(
    waitForHealth({
      url: 'http://127.0.0.1:8002/api/health',
      now: () => currentTime,
      timeoutMs: 200,
      intervalMs: 100,
      fetchImpl: async () => {
        currentTime += 100
        throw new Error('not ready')
      },
      delay: async () => {},
    }),
    /timed out/,
  )
})
