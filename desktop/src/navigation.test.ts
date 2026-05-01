import assert from 'node:assert/strict'
import test from 'node:test'

import { isAllowedAppNavigation, shouldOpenExternally } from './navigation.js'

const targetUrl = 'http://127.0.0.1:8002'

test('isAllowedAppNavigation allows same-origin backend pages', () => {
  assert.equal(isAllowedAppNavigation(targetUrl, 'http://127.0.0.1:8002/api/health'), true)
})

test('isAllowedAppNavigation rejects prefix lookalike ports', () => {
  assert.equal(isAllowedAppNavigation(targetUrl, 'http://127.0.0.1:80020/'), false)
})

test('shouldOpenExternally only opens http and https URLs outside the app origin', () => {
  assert.equal(shouldOpenExternally(targetUrl, 'https://example.test'), true)
  assert.equal(shouldOpenExternally(targetUrl, 'http://127.0.0.1:8002/game'), false)
  assert.equal(shouldOpenExternally(targetUrl, 'file:///C:/Windows/System32/calc.exe'), false)
  assert.equal(shouldOpenExternally(targetUrl, 'javascript:alert(1)'), false)
})
