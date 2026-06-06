import { spawn, spawnSync, type ChildProcess } from 'node:child_process'
import fs from 'node:fs'
import net from 'node:net'
import os from 'node:os'
import path from 'node:path'

type TaskkillRunner = (pid: number) => void

export interface BackendEnvOptions {
  port: number
  baseEnv?: NodeJS.ProcessEnv
  seedEnv?: NodeJS.ProcessEnv
}

export interface StartBackendOptions {
  executable: string
  port: number
  logDir: string
  baseEnv?: NodeJS.ProcessEnv
  seedEnv?: NodeJS.ProcessEnv
}

export interface StopBackendOptions {
  platform?: NodeJS.Platform
  taskkillRunner?: TaskkillRunner
}

const TRUE_ENV = '1'

export function buildBackendEnv(options: BackendEnvOptions): NodeJS.ProcessEnv {
  return {
    ...(options.baseEnv ?? process.env),
    ...(options.seedEnv ?? {}),
    SERVER_HOST: '127.0.0.1',
    SERVER_PORT: String(options.port),
    CWS_NO_BROWSER: TRUE_ENV,
    CWS_DISABLE_AUTO_SHUTDOWN: TRUE_ENV,
    PYTHONUTF8: (options.baseEnv ?? process.env).PYTHONUTF8 || TRUE_ENV,
    PYTHONIOENCODING: (options.baseEnv ?? process.env).PYTHONIOENCODING || 'utf-8',
  }
}

export async function findFreePort(startPort = 8002, endPort = 8102): Promise<number> {
  for (let port = startPort; port <= endPort; port += 1) {
    if (await canBind(port)) return port
  }
  throw new Error(`No free port found in range ${startPort}-${endPort}`)
}

function canBind(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const server = net.createServer()
    server.once('error', () => resolve(false))
    server.once('listening', () => {
      server.close(() => resolve(true))
    })
    server.listen(port, '127.0.0.1')
  })
}

export function startBackend(options: StartBackendOptions): ChildProcess {
  if (!fs.existsSync(options.executable)) {
    throw new Error(`Backend executable not found: ${options.executable}`)
  }

  fs.mkdirSync(options.logDir, { recursive: true })
  const out = fs.openSync(path.join(options.logDir, 'backend.stdout.log'), 'a')
  const err = fs.openSync(path.join(options.logDir, 'backend.stderr.log'), 'a')

  return spawn(options.executable, [], {
    cwd: path.dirname(options.executable),
    env: buildBackendEnv({
      port: options.port,
      baseEnv: options.baseEnv,
      seedEnv: options.seedEnv,
    }),
    windowsHide: true,
    detached: false,
    stdio: ['ignore', out, err],
  })
}

function runTaskkill(pid: number): void {
  spawnSync('taskkill', ['/pid', String(pid), '/t', '/f'], {
    windowsHide: true,
    stdio: 'ignore',
  })
}

export function stopBackend(processRef: ChildProcess | undefined, options: StopBackendOptions = {}): boolean {
  if (!processRef || processRef.killed) return false

  const platform = options.platform ?? process.platform

  if (platform === 'win32' && processRef.pid) {
    const taskkillRunner = options.taskkillRunner ?? runTaskkill
    taskkillRunner(processRef.pid)
    return true
  }

  processRef.kill('SIGTERM')
  return true
}

export function getDefaultLogDir(appName = 'CultivationWorldSimulator'): string {
  const base = process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local')
  return path.join(base, appName, 'logs', 'electron')
}

export function collectSeedEnv(baseEnv: NodeJS.ProcessEnv = process.env): NodeJS.ProcessEnv {
  const seedEnv: NodeJS.ProcessEnv = {}
  for (const [key, value] of Object.entries(baseEnv)) {
    if (key.startsWith('CWS_DEFAULT_LLM_') && value) {
      seedEnv[key] = value
    }
  }
  return seedEnv
}
