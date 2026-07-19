import fs from 'node:fs'
import path from 'node:path'

export type DesktopDistribution = 'generic' | 'epic'

export interface DesktopDistributionManifest {
  distribution: DesktopDistribution
  features: {
    epicEosMetrics: boolean
  }
}

const DEFAULT_MANIFEST: DesktopDistributionManifest = {
  distribution: 'generic',
  features: {
    epicEosMetrics: false,
  },
}

function isDistribution(value: unknown): value is DesktopDistribution {
  return value === 'generic' || value === 'epic'
}

export function getDistributionManifestPath(resourcesPath: string): string {
  return path.join(resourcesPath, 'desktop-distribution.json')
}

export function readDistributionManifest(manifestPath: string): DesktopDistributionManifest {
  if (!fs.existsSync(manifestPath)) {
    return DEFAULT_MANIFEST
  }

  try {
    const raw = JSON.parse(fs.readFileSync(manifestPath, 'utf8')) as {
      distribution?: unknown
      features?: {
        epicEosMetrics?: unknown
      }
    }

    return {
      distribution: isDistribution(raw.distribution) ? raw.distribution : DEFAULT_MANIFEST.distribution,
      features: {
        epicEosMetrics: raw.features?.epicEosMetrics === true,
      },
    }
  }
  catch {
    return DEFAULT_MANIFEST
  }
}

export function isEpicEosMetricsEnabled(manifest: DesktopDistributionManifest): boolean {
  return manifest.distribution === 'epic' && manifest.features.epicEosMetrics === true
}
