import assert from 'node:assert/strict'
import type { ChildProcess } from 'node:child_process'
import { EventEmitter } from 'node:events'
import test from 'node:test'

import { createBackendController, installBackendCleanupHooks } from './backendLifecycle.js'

class FakeChildProcess extends EventEmitter {
  pid: number
  killed = false

  constructor(pid: number) {
    super()
    this.pid = pid
  }

  kill(): boolean {
    this.killed = true
    return true
  }
}

class FakeLifecycleProcess extends EventEmitter {
  exitCodes: number[] = []

  exit(code?: number): never {
    this.exitCodes.push(code ?? 0)
    throw new Error('fake process exit')
  }
}

test('backend controller cleans the active backend once', () => {
  const stoppedPids: number[] = []
  const controller = createBackendController({
    stop: (processRef) => {
      stoppedPids.push(processRef?.pid ?? -1)
      return true
    },
  })
  const processRef = new FakeChildProcess(101) as unknown as ChildProcess

  controller.set(processRef)
  assert.equal(controller.get(), processRef)

  controller.cleanup()
  controller.cleanup()

  assert.deepEqual(stoppedPids, [101])
  assert.equal(controller.get(), undefined)
})

test('backend controller clears the backend reference when it exits first', () => {
  const stoppedPids: number[] = []
  const controller = createBackendController({
    stop: (processRef) => {
      stoppedPids.push(processRef?.pid ?? -1)
      return true
    },
  })
  const processRef = new FakeChildProcess(102) as unknown as ChildProcess

  controller.set(processRef)
  processRef.emit('exit', 0, null)
  controller.cleanup()

  assert.equal(controller.get(), undefined)
  assert.deepEqual(stoppedPids, [])
})

test('backend controller stops processes registered after cleanup was requested', () => {
  const stoppedPids: number[] = []
  const controller = createBackendController({
    stop: (processRef) => {
      stoppedPids.push(processRef?.pid ?? -1)
      return true
    },
  })
  const processRef = new FakeChildProcess(103) as unknown as ChildProcess

  controller.cleanup()
  controller.set(processRef)

  assert.deepEqual(stoppedPids, [103])
  assert.equal(controller.get(), undefined)
})

test('backend cleanup hooks cover Electron and process shutdown paths idempotently', () => {
  const app = new EventEmitter()
  const processRef = new FakeLifecycleProcess()
  let cleanupCount = 0

  installBackendCleanupHooks({
    app,
    processRef,
    cleanup: () => {
      cleanupCount += 1
    },
  })

  app.emit('before-quit')
  app.emit('will-quit')
  app.emit('quit')
  processRef.emit('exit')

  assert.equal(cleanupCount, 1)
})

for (const eventName of ['before-quit', 'will-quit', 'quit'] as const) {
  test(`backend cleanup hook runs when ${eventName} is the first Electron shutdown event`, () => {
    const app = new EventEmitter()
    const processRef = new FakeLifecycleProcess()
    let cleanupCount = 0

    installBackendCleanupHooks({
      app,
      processRef,
      cleanup: () => {
        cleanupCount += 1
      },
    })

    app.emit(eventName)

    assert.equal(cleanupCount, 1)
  })
}

test('backend cleanup hook runs when process exit is the first shutdown event', () => {
  const app = new EventEmitter()
  const processRef = new FakeLifecycleProcess()
  let cleanupCount = 0

  installBackendCleanupHooks({
    app,
    processRef,
    cleanup: () => {
      cleanupCount += 1
    },
  })

  processRef.emit('exit')

  assert.equal(cleanupCount, 1)
})

test('backend cleanup hooks clean up before process signal exit', () => {
  const app = new EventEmitter()
  const processRef = new FakeLifecycleProcess()
  let cleanupCount = 0

  installBackendCleanupHooks({
    app,
    processRef,
    cleanup: () => {
      cleanupCount += 1
    },
  })

  assert.throws(() => processRef.emit('SIGTERM'), /fake process exit/)
  assert.equal(cleanupCount, 1)
  assert.deepEqual(processRef.exitCodes, [0])
})
