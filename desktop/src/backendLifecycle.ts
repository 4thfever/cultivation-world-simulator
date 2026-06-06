import type { ChildProcess } from 'node:child_process'

import { stopBackend } from './backend.js'

type CleanupHandler = () => void
type SignalName = 'SIGINT' | 'SIGTERM' | 'SIGHUP'

export interface BackendLifecycleApp {
  on(eventName: 'before-quit' | 'will-quit' | 'quit', listener: CleanupHandler): unknown
}

export interface BackendLifecycleProcess {
  once(eventName: 'exit' | SignalName, listener: CleanupHandler): unknown
  exit(code?: number): never
}

export interface BackendControllerOptions {
  stop?: typeof stopBackend
}

export interface BackendCleanupHookOptions {
  app: BackendLifecycleApp
  processRef: BackendLifecycleProcess
  cleanup: CleanupHandler
}

export function createBackendController(options: BackendControllerOptions = {}) {
  let backendProcess: ChildProcess | undefined
  let cleanupStarted = false
  const stop = options.stop ?? stopBackend

  function set(processRef: ChildProcess): void {
    if (cleanupStarted) {
      stop(processRef)
      return
    }

    backendProcess = processRef
    processRef.once('exit', () => {
      if (backendProcess === processRef) {
        backendProcess = undefined
      }
    })
  }

  function get(): ChildProcess | undefined {
    return backendProcess
  }

  function cleanup(): void {
    if (cleanupStarted) return
    cleanupStarted = true

    const processToStop = backendProcess
    backendProcess = undefined
    if (processToStop) {
      stop(processToStop)
    }
  }

  return {
    set,
    get,
    cleanup,
  }
}

export function installBackendCleanupHooks(options: BackendCleanupHookOptions): void {
  const { app, processRef, cleanup } = options
  let cleanupDone = false

  function cleanupOnce(): void {
    if (cleanupDone) return
    cleanupDone = true
    cleanup()
  }

  app.on('before-quit', cleanupOnce)
  app.on('will-quit', cleanupOnce)
  app.on('quit', cleanupOnce)
  processRef.once('exit', cleanupOnce)

  for (const signal of ['SIGINT', 'SIGTERM', 'SIGHUP'] as SignalName[]) {
    processRef.once(signal, () => {
      cleanupOnce()
      processRef.exit(0)
    })
  }
}
