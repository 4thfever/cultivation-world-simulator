import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'

import {
  maskSensitiveText,
  mergeLauncherFallbacks,
  parseEpicLauncherArgs,
  readEpicRuntimeConfig,
} from './epicRuntime.js'

test('readEpicRuntimeConfig returns undefined for missing or incomplete config', () => {
  assert.equal(readEpicRuntimeConfig(path.join(os.tmpdir(), 'missing-eos-runtime.json')), undefined)

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cws-eos-runtime-'))
  const configPath = path.join(dir, 'eos-runtime.json')
  fs.writeFileSync(configPath, JSON.stringify({
    productId: 'product',
    deploymentId: 'deployment',
  }))

  assert.equal(readEpicRuntimeConfig(configPath), undefined)
})

test('readEpicRuntimeConfig parses required runtime fields', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cws-eos-runtime-'))
  const configPath = path.join(dir, 'eos-runtime.json')
  fs.writeFileSync(configPath, JSON.stringify({
    environment: 'dev',
    productId: 'product',
    sandboxId: 'sandbox',
    deploymentId: 'deployment',
    clientId: 'client',
    clientSecret: 'secret',
  }))

  assert.deepEqual(readEpicRuntimeConfig(configPath), {
    environment: 'dev',
    productId: 'product',
    sandboxId: 'sandbox',
    deploymentId: 'deployment',
    clientId: 'client',
    clientSecret: 'secret',
  })
})

test('parseEpicLauncherArgs accepts equals and separated values', () => {
  const args = parseEpicLauncherArgs([
    '-epicdeploymentid=launcher-deployment',
    '-epicsandboxid',
    'launcher-sandbox',
    '-AUTH_LOGIN=user',
    '-AUTH_PASSWORD',
    'exchange-code',
    '-AUTH_TYPE=exchangecode',
  ])

  assert.deepEqual(args, {
    deploymentId: 'launcher-deployment',
    sandboxId: 'launcher-sandbox',
    authLogin: 'user',
    authPassword: 'exchange-code',
    authType: 'exchangecode',
  })
})

test('mergeLauncherFallbacks lets launcher deployment override packaged fallback', () => {
  const merged = mergeLauncherFallbacks(
    {
      productId: 'product',
      sandboxId: 'packaged-sandbox',
      deploymentId: 'packaged-deployment',
      clientId: 'client',
      clientSecret: 'secret',
    },
    {
      deploymentId: 'launcher-deployment',
    },
  )

  assert.equal(merged.sandboxId, 'packaged-sandbox')
  assert.equal(merged.deploymentId, 'launcher-deployment')
})

test('maskSensitiveText redacts launcher auth password and client secret', () => {
  const masked = maskSensitiveText(
    '-AUTH_PASSWORD=exchange-code {"clientSecret":"secret","authPassword":"another"}',
  )

  assert.equal(masked.includes('exchange-code'), false)
  assert.equal(masked.includes('secret'), false)
  assert.equal(masked.includes('another'), false)
  assert.equal(masked.includes('[redacted]'), true)
})
