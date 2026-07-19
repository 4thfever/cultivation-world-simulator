import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'

import { isEpicEosMetricsEnabled, readDistributionManifest } from './distribution.js'

test('missing distribution manifest defaults to generic with Epic EOS disabled', () => {
  const manifest = readDistributionManifest(path.join(os.tmpdir(), 'missing-cws-distribution.json'))

  assert.equal(manifest.distribution, 'generic')
  assert.equal(manifest.features.epicEosMetrics, false)
  assert.equal(isEpicEosMetricsEnabled(manifest), false)
})

test('Epic distribution enables metrics only when the feature flag is true', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cws-distribution-'))
  const manifestPath = path.join(dir, 'desktop-distribution.json')
  fs.writeFileSync(manifestPath, JSON.stringify({
    distribution: 'epic',
    features: {
      epicEosMetrics: true,
    },
  }))

  const manifest = readDistributionManifest(manifestPath)

  assert.equal(manifest.distribution, 'epic')
  assert.equal(manifest.features.epicEosMetrics, true)
  assert.equal(isEpicEosMetricsEnabled(manifest), true)
})

test('malformed distribution manifest falls back to generic behavior', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cws-distribution-'))
  const manifestPath = path.join(dir, 'desktop-distribution.json')
  fs.writeFileSync(manifestPath, '{bad json')

  const manifest = readDistributionManifest(manifestPath)

  assert.equal(manifest.distribution, 'generic')
  assert.equal(manifest.features.epicEosMetrics, false)
})
