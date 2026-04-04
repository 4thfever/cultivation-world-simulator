import type { RegionSummary } from '@/types/core';
import { getRegionTextMetrics, usesCompactMapLabels } from '@/utils/mapStyles';

const TILE_SIZE = 64;
const AVG_LATIN_GLYPH_WIDTH_RATIO = 0.58;
const AVG_COMPACT_GLYPH_WIDTH_RATIO = 0.96;
const LABEL_BOX_PADDING_X = 10;
const LABEL_BOX_PADDING_Y = 6;
const LABEL_COLLISION_PADDING = 8;
const LATIN_WRAP_TARGET = 16;

export type MapRegionLabel = RegionSummary & {
  displayName: string;
  labelX: number;
  labelY: number;
  priority: number;
};

type LabelBounds = {
  left: number;
  top: number;
  right: number;
  bottom: number;
};

function getRegionPriority(region: RegionSummary): number {
  switch (region.type) {
    case 'city':
      return 4;
    case 'sect':
      return 3;
    case 'cultivate':
      return 2;
    default:
      return 1;
  }
}

function splitLatinWords(name: string): string[] {
  return name
    .trim()
    .split(/\s+/)
    .filter(Boolean);
}

function truncateWithEllipsis(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;
  return `${text.slice(0, Math.max(1, maxChars - 1)).trimEnd()}…`;
}

export function formatRegionDisplayName(name: string, locale: string): string {
  if (usesCompactMapLabels(locale)) {
    return name;
  }

  const words = splitLatinWords(name);
  if (words.length <= 1) {
    return truncateWithEllipsis(name, LATIN_WRAP_TARGET);
  }

  let firstLine = '';
  let secondLineWords: string[] = [];

  for (const word of words) {
    const candidate = firstLine ? `${firstLine} ${word}` : word;
    if (candidate.length <= LATIN_WRAP_TARGET || firstLine.length === 0) {
      firstLine = candidate;
      continue;
    }
    secondLineWords = words.slice(words.indexOf(word));
    break;
  }

  if (secondLineWords.length === 0) {
    return firstLine;
  }

  const secondLine = truncateWithEllipsis(secondLineWords.join(' '), LATIN_WRAP_TARGET);
  return `${firstLine}\n${secondLine}`;
}

function estimateLabelBounds(region: RegionSummary, displayName: string, locale: string): LabelBounds {
  const metrics = getRegionTextMetrics(region.type, locale);
  const lines = displayName.split('\n');
  const maxChars = Math.max(...lines.map((line) => line.length), 1);
  const widthRatio = usesCompactMapLabels(locale)
    ? AVG_COMPACT_GLYPH_WIDTH_RATIO
    : AVG_LATIN_GLYPH_WIDTH_RATIO;
  const width = maxChars * metrics.fontSize * widthRatio + LABEL_BOX_PADDING_X * 2;
  const height = lines.length * metrics.lineHeight + LABEL_BOX_PADDING_Y * 2;
  const centerX = region.x * TILE_SIZE + TILE_SIZE / 2;
  const centerY = region.y * TILE_SIZE + TILE_SIZE * 1.5;

  return {
    left: centerX - width / 2 - LABEL_COLLISION_PADDING,
    right: centerX + width / 2 + LABEL_COLLISION_PADDING,
    top: centerY - height / 2 - LABEL_COLLISION_PADDING,
    bottom: centerY + height / 2 + LABEL_COLLISION_PADDING
  };
}

function intersects(a: LabelBounds, b: LabelBounds): boolean {
  return !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom);
}

export function buildVisibleRegionLabels(
  regions: RegionSummary[],
  locale: string
): MapRegionLabel[] {
  const sortedRegions = [...regions].sort((a, b) => {
    const priorityDiff = getRegionPriority(b) - getRegionPriority(a);
    if (priorityDiff !== 0) return priorityDiff;

    const nameLengthDiff = a.name.length - b.name.length;
    if (nameLengthDiff !== 0) return nameLengthDiff;

    return String(a.id).localeCompare(String(b.id));
  });

  const accepted: Array<{ label: MapRegionLabel; bounds: LabelBounds }> = [];

  for (const region of sortedRegions) {
    const displayName = formatRegionDisplayName(region.name, locale);
    const bounds = estimateLabelBounds(region, displayName, locale);
    const overlapped = accepted.some((entry) => intersects(entry.bounds, bounds));
    if (overlapped) {
      continue;
    }

    accepted.push({
      label: {
        ...region,
        displayName,
        labelX: region.x * TILE_SIZE + TILE_SIZE / 2,
        labelY: region.y * TILE_SIZE + TILE_SIZE * 1.5,
        priority: getRegionPriority(region)
      },
      bounds
    });
  }

  return accepted.map((entry) => entry.label);
}
