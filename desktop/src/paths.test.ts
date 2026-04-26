import assert from 'node:assert/strict'
import path from 'node:path'
import test from 'node:test'

import { normalizeHttpUrl, resolvePackagedBackendExe } from './paths.js'

test('resolvePackagedBackendExe points at resources backend directory', () => {
  const exe = resolvePackagedBackendExe({
    resourcesPath: path.join('C:', 'game', 'resources'),
  })

  assert.equal(exe, path.join('C:', 'game', 'resources', 'backend', 'AICultivationSimulator_Steam.exe'))
})

test('normalizeHttpUrl uses localhost loopback by default', () => {
  assert.equal(normalizeHttpUrl(8002), 'http://127.0.0.1:8002')
})
