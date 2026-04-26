import path from 'node:path'

export const BACKEND_EXE_NAME = 'AICultivationSimulator_Steam.exe'

export interface BackendPathOptions {
  resourcesPath: string
  backendDir?: string
  backendExeName?: string
}

export function resolvePackagedBackendExe(options: BackendPathOptions): string {
  const backendDir = options.backendDir ?? 'backend'
  const exeName = options.backendExeName ?? BACKEND_EXE_NAME
  return path.join(options.resourcesPath, backendDir, exeName)
}

export function normalizeHttpUrl(port: number, host = '127.0.0.1'): string {
  return `http://${host}:${port}`
}
