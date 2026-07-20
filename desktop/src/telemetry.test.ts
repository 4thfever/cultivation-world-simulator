import assert from 'node:assert/strict'
import type { ChildProcess, SpawnOptionsWithoutStdio } from 'node:child_process'
import { EventEmitter } from 'node:events'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'

import { NullTelemetryProvider } from './telemetry.js'
import { createTelemetryProvider, EpicEosTelemetryProvider } from './telemetry.js'

class FakeChildProcess extends EventEmitter {
  killed = false
  writes: string[] = []
  stdin = {
    write: (value: string) => {
      this.writes.push(value)
      return true
    },
    end: () => {
      this.killed = true
    },
  }
}

function makeRuntimeDir(options: { epicEnabled: boolean; config?: Record<string, unknown> }) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cws-telemetry-'))
  fs.writeFileSync(path.join(dir, 'desktop-distribution.json'), JSON.stringify({
    distribution: options.epicEnabled ? 'epic' : 'generic',
    features: {
      epicEosMetrics: options.epicEnabled,
    },
  }))

  if (options.config) {
    fs.writeFileSync(path.join(dir, 'eos-runtime.json'), JSON.stringify(options.config))
  }

  return dir
}

test('createTelemetryProvider returns NullTelemetryProvider for generic distribution', () => {
  const resourcesPath = makeRuntimeDir({ epicEnabled: false })

  const provider = createTelemetryProvider({
    resourcesPath,
    logDir: resourcesPath,
  })

  assert.equal(provider instanceof NullTelemetryProvider, true)
})

test('createTelemetryProvider returns Epic provider when manifest enables Epic EOS metrics', () => {
  const resourcesPath = makeRuntimeDir({ epicEnabled: true })

  const provider = createTelemetryProvider({
    resourcesPath,
    logDir: resourcesPath,
  })

  assert.equal(provider instanceof EpicEosTelemetryProvider, true)
})

test('Epic provider disables itself when helper is missing', async () => {
  const warnings: string[] = []
  const resourcesPath = makeRuntimeDir({
    epicEnabled: true,
    config: {
      productId: 'product',
      deploymentId: 'deployment',
      clientId: 'client',
      clientSecret: 'secret',
    },
  })

  const provider = createTelemetryProvider({
    resourcesPath,
    logDir: resourcesPath,
    log: {
      info: () => {},
      warn: (message) => warnings.push(message),
      error: () => {},
    },
  })

  await provider.beginSession()

  assert.equal(warnings.some((message) => message.includes('helper not found')), true)
})

test('Epic provider sends begin and end session messages to helper', async () => {
  const resourcesPath = makeRuntimeDir({
    epicEnabled: true,
    config: {
      productId: 'product',
      sandboxId: 'packaged-sandbox',
      deploymentId: 'packaged-deployment',
      clientId: 'client',
      clientSecret: 'secret',
    },
  })
  const helperPath = path.join(resourcesPath, 'eos-helper', 'eos-helper.exe')
  fs.mkdirSync(path.dirname(helperPath), { recursive: true })
  fs.writeFileSync(helperPath, '')

  const fakeProcess = new FakeChildProcess()
  const spawnCalls: Array<{ command: string; options: SpawnOptionsWithoutStdio }> = []
  const spawnImpl = ((command: string, _args: readonly string[], options: SpawnOptionsWithoutStdio) => {
    spawnCalls.push({ command, options })
    return fakeProcess as unknown as ChildProcess
  }) as typeof import('node:child_process').spawn

  const provider = createTelemetryProvider({
    resourcesPath,
    logDir: resourcesPath,
    argv: [
      '-epicdeploymentid=launcher-deployment',
      '-AUTH_PASSWORD=exchange-code',
      '-AUTH_TYPE=exchangecode',
    ],
    spawnImpl,
  })

  await provider.beginSession()
  await provider.endSession()
  await provider.shutdown()

  assert.equal(spawnCalls.length, 1)
  assert.equal(spawnCalls[0].command, helperPath)
  assert.equal(fakeProcess.writes.length, 2)

  const beginMessage = JSON.parse(fakeProcess.writes[0]) as {
    type: string
    config: {
      deploymentId: string
    }
  }
  const endMessage = JSON.parse(fakeProcess.writes[1]) as { type: string }

  assert.equal(beginMessage.type, 'begin-session')
  assert.equal(beginMessage.config.deploymentId, 'launcher-deployment')
  assert.equal(JSON.stringify(beginMessage).includes('exchange-code'), false)
  assert.equal(endMessage.type, 'end-session')
  assert.equal(fakeProcess.killed, true)
})
