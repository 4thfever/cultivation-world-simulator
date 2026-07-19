import fs from 'node:fs'
import path from 'node:path'

export interface EpicRuntimeConfig {
  environment?: string
  productId: string
  sandboxId?: string
  deploymentId: string
  clientId: string
  clientSecret: string
}

export interface EpicLauncherArgs {
  deploymentId?: string
  sandboxId?: string
  authLogin?: string
  authPassword?: string
  authType?: string
}

export function getEpicRuntimeConfigPath(resourcesPath: string): string {
  return path.join(resourcesPath, 'eos-runtime.json')
}

export function getEpicHelperExePath(resourcesPath: string): string {
  return path.join(resourcesPath, 'eos-helper', 'eos-helper.exe')
}

function readString(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

export function readEpicRuntimeConfig(configPath: string): EpicRuntimeConfig | undefined {
  if (!fs.existsSync(configPath)) {
    return undefined
  }

  try {
    const raw = JSON.parse(fs.readFileSync(configPath, 'utf8')) as Record<string, unknown>
    const config: EpicRuntimeConfig = {
      environment: readString(raw.environment) || undefined,
      productId: readString(raw.productId),
      sandboxId: readString(raw.sandboxId) || undefined,
      deploymentId: readString(raw.deploymentId),
      clientId: readString(raw.clientId),
      clientSecret: readString(raw.clientSecret),
    }

    if (!config.productId || !config.deploymentId || !config.clientId || !config.clientSecret) {
      return undefined
    }
    return config
  }
  catch {
    return undefined
  }
}

function normalizeKey(rawKey: string): string {
  return rawKey.replace(/^-+/, '').toLowerCase()
}

export function parseEpicLauncherArgs(argv: readonly string[]): EpicLauncherArgs {
  const args: EpicLauncherArgs = {}

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index]
    if (!token.startsWith('-')) continue

    const withoutPrefix = token.replace(/^-+/, '')
    const equalsIndex = withoutPrefix.indexOf('=')
    const key = normalizeKey(equalsIndex >= 0 ? withoutPrefix.slice(0, equalsIndex) : withoutPrefix)
    let value = equalsIndex >= 0 ? withoutPrefix.slice(equalsIndex + 1) : ''
    if (!value && index + 1 < argv.length && !argv[index + 1].startsWith('-')) {
      value = argv[index + 1]
      index += 1
    }

    if (!value) continue

    if (key === 'epicdeploymentid') args.deploymentId = value
    else if (key === 'epicsandboxid') args.sandboxId = value
    else if (key === 'auth_login') args.authLogin = value
    else if (key === 'auth_password') args.authPassword = value
    else if (key === 'auth_type') args.authType = value
  }

  return args
}

export function mergeLauncherFallbacks(config: EpicRuntimeConfig, launcherArgs: EpicLauncherArgs): EpicRuntimeConfig {
  return {
    ...config,
    sandboxId: launcherArgs.sandboxId || config.sandboxId,
    deploymentId: launcherArgs.deploymentId || config.deploymentId,
  }
}

export function maskSensitiveText(value: string): string {
  return value
    .replace(/(-AUTH_PASSWORD=)[^\s]+/gi, '$1[redacted]')
    .replace(/(-AUTH_PASSWORD\s+)[^\s]+/gi, '$1[redacted]')
    .replace(/("clientSecret"\s*:\s*")[^"]+(")/gi, '$1[redacted]$2')
    .replace(/("authPassword"\s*:\s*")[^"]+(")/gi, '$1[redacted]$2')
}
