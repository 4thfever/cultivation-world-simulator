import { spawn, type ChildProcess } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

import { getDistributionManifestPath, isEpicEosMetricsEnabled, readDistributionManifest } from './distribution.js'
import {
  getEpicHelperExePath,
  getEpicRuntimeConfigPath,
  maskSensitiveText,
  mergeLauncherFallbacks,
  parseEpicLauncherArgs,
  readEpicRuntimeConfig,
} from './epicRuntime.js'

export interface TelemetryProvider {
  beginSession(): Promise<void>
  endSession(): Promise<void>
  shutdown(): Promise<void>
}

export interface TelemetryLog {
  info(message: string): void
  warn(message: string): void
  error(message: string): void
}

export interface CreateTelemetryProviderOptions {
  resourcesPath: string
  logDir: string
  argv?: readonly string[]
  fsExists?: (targetPath: string) => boolean
  spawnImpl?: typeof spawn
  log?: TelemetryLog
}

interface EpicEosTelemetryProviderOptions {
  helperExe: string
  configPath: string
  logDir: string
  argv: readonly string[]
  fsExists: (targetPath: string) => boolean
  spawnImpl: typeof spawn
  log: TelemetryLog
}

const NOOP_LOG: TelemetryLog = {
  info: () => {},
  warn: () => {},
  error: () => {},
}

export class NullTelemetryProvider implements TelemetryProvider {
  async beginSession(): Promise<void> {}
  async endSession(): Promise<void> {}
  async shutdown(): Promise<void> {}
}

export class EpicEosTelemetryProvider implements TelemetryProvider {
  private processRef: ChildProcess | undefined
  private sessionStarted = false

  constructor(private readonly options: EpicEosTelemetryProviderOptions) {}

  async beginSession(): Promise<void> {
    if (this.processRef) return

    if (!this.options.fsExists(this.options.helperExe)) {
      this.options.log.warn(`Epic EOS helper not found: ${this.options.helperExe}`)
      return
    }
    if (!this.options.fsExists(this.options.configPath)) {
      this.options.log.warn(`Epic EOS runtime config not found: ${this.options.configPath}`)
      return
    }

    const config = readEpicRuntimeConfig(this.options.configPath)
    if (!config) {
      this.options.log.warn('Epic EOS runtime config is missing required fields.')
      return
    }

    const launcherArgs = parseEpicLauncherArgs(this.options.argv)
    const runtimeConfig = mergeLauncherFallbacks(config, launcherArgs)

    try {
      fs.mkdirSync(this.options.logDir, { recursive: true })
      const stdout = fs.openSync(path.join(this.options.logDir, 'eos-helper.stdout.log'), 'a')
      const stderr = fs.openSync(path.join(this.options.logDir, 'eos-helper.stderr.log'), 'a')

      this.processRef = this.options.spawnImpl(this.options.helperExe, [], {
        cwd: path.dirname(this.options.helperExe),
        windowsHide: true,
        stdio: ['pipe', stdout, stderr],
      })

      this.processRef.once('exit', () => {
        this.processRef = undefined
        this.sessionStarted = false
      })

      this.writeMessage({
        type: 'begin-session',
        config: runtimeConfig,
        launcherArgs,
      })
      this.sessionStarted = true
      this.options.log.info('Epic EOS Metrics begin-session message sent.')
    }
    catch (error) {
      this.processRef = undefined
      this.sessionStarted = false
      this.options.log.warn(`Epic EOS Metrics disabled after helper startup failure: ${formatError(error)}`)
    }
  }

  async endSession(): Promise<void> {
    if (!this.processRef || !this.sessionStarted) return
    this.writeMessage({
      type: 'end-session',
    })
    this.sessionStarted = false
    this.options.log.info('Epic EOS Metrics end-session message sent.')
  }

  async shutdown(): Promise<void> {
    await this.endSession()
    const processToStop = this.processRef
    this.processRef = undefined
    if (!processToStop || processToStop.killed) return

    try {
      processToStop.stdin?.end()
    }
    catch {}
  }

  private writeMessage(message: unknown): void {
    const serialized = JSON.stringify(message)
    this.processRef?.stdin?.write(`${serialized}\n`)
  }
}

export function createTelemetryProvider(options: CreateTelemetryProviderOptions): TelemetryProvider {
  const log = options.log ?? NOOP_LOG
  const fsExists = options.fsExists ?? fs.existsSync
  const manifestPath = getDistributionManifestPath(options.resourcesPath)
  const manifest = readDistributionManifest(manifestPath)

  if (!isEpicEosMetricsEnabled(manifest)) {
    return new NullTelemetryProvider()
  }

  return new EpicEosTelemetryProvider({
    helperExe: getEpicHelperExePath(options.resourcesPath),
    configPath: getEpicRuntimeConfigPath(options.resourcesPath),
    logDir: options.logDir,
    argv: options.argv ?? process.argv,
    fsExists,
    spawnImpl: options.spawnImpl ?? spawn,
    log,
  })
}

export function createFileTelemetryLog(logDir: string): TelemetryLog {
  function append(level: string, message: string): void {
    try {
      fs.mkdirSync(logDir, { recursive: true })
      const line = `${new Date().toISOString()} [${level}] ${maskSensitiveText(message)}\n`
      fs.appendFileSync(path.join(logDir, 'telemetry.log'), line, 'utf8')
    }
    catch {}
  }

  return {
    info: (message) => append('info', message),
    warn: (message) => append('warn', message),
    error: (message) => append('error', message),
  }
}

function formatError(error: unknown): string {
  if (error instanceof Error) {
    return maskSensitiveText(error.message)
  }
  return maskSensitiveText(String(error))
}
