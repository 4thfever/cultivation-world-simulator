import type { RegionSummary } from '@/types/core';
import { getRegionTextMetrics, usesCompactMapLabels } from '@/utils/mapStyles';

const TILE_SIZE = 64;
const LATIN_WRAP_TARGET = 16;
const AVG_LATIN_GLYPH_WIDTH_RATIO = 0.58;
const AVG_COMPACT_GLYPH_WIDTH_RATIO = 0.96;
const LABEL_BOX_PADDING_X = 10;
const LABEL_BOX_PADDING_Y = 6;
const LABEL_COLLISION_PADDING = 8;
const SPATIAL_BUCKET_SIZE = 256;

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

type LabelPlacement = {
  labelX: number;
  labelY: number;
  bounds: LabelBounds;
};

type AcceptedLabel = {
  label: MapRegionLabel;
  bounds: LabelBounds;
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

function estimateLabelPlacement(
  region: RegionSummary,
  displayName: string,
  locale: string,
  offsetX = 0,
  offsetY = 0
): LabelPlacement {
  const metrics = getRegionTextMetrics(region.type, locale);
  const lines = displayName.split('\n');
  const maxChars = Math.max(...lines.map((line) => line.length), 1);
  const widthRatio = usesCompactMapLabels(locale)
    ? AVG_COMPACT_GLYPH_WIDTH_RATIO
    : AVG_LATIN_GLYPH_WIDTH_RATIO;
  const width = maxChars * metrics.fontSize * widthRatio + LABEL_BOX_PADDING_X * 2;
  const height = lines.length * metrics.lineHeight + LABEL_BOX_PADDING_Y * 2;
  const labelX = region.x * TILE_SIZE + TILE_SIZE / 2 + offsetX;
  const labelY = region.y * TILE_SIZE + TILE_SIZE * 1.5 + offsetY;

  return {
    labelX,
    labelY,
    bounds: {
      left: labelX - width / 2 - LABEL_COLLISION_PADDING,
      right: labelX + width / 2 + LABEL_COLLISION_PADDING,
      top: labelY - height / 2 - LABEL_COLLISION_PADDING,
      bottom: labelY + height / 2 + LABEL_COLLISION_PADDING
    }
  };
}

function intersects(a: LabelBounds, b: LabelBounds): boolean {
  return !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom);
}

function getBucketKey(x: number, y: number): string {
  return `${x},${y}`;
}

function getBoundsBucketRange(bounds: LabelBounds) {
  return {
    minX: Math.floor(bounds.left / SPATIAL_BUCKET_SIZE),
    maxX: Math.floor(bounds.right / SPATIAL_BUCKET_SIZE),
    minY: Math.floor(bounds.top / SPATIAL_BUCKET_SIZE),
    maxY: Math.floor(bounds.bottom / SPATIAL_BUCKET_SIZE)
  };
}

function findCollision(
  bounds: LabelBounds,
  spatialIndex: Map<string, AcceptedLabel[]>
): AcceptedLabel | undefined {
  const range = getBoundsBucketRange(bounds);

  for (let x = range.minX; x <= range.maxX; x += 1) {
    for (let y = range.minY; y <= range.maxY; y += 1) {
      const bucket = spatialIndex.get(getBucketKey(x, y));
      if (!bucket) continue;

      const hit = bucket.find((entry) => intersects(entry.bounds, bounds));
      if (hit) {
        return hit;
      }
    }
  }

  return undefined;
}

function addToSpatialIndex(entry: AcceptedLabel, spatialIndex: Map<string, AcceptedLabel[]>) {
  const range = getBoundsBucketRange(entry.bounds);

  for (let x = range.minX; x <= range.maxX; x += 1) {
    for (let y = range.minY; y <= range.maxY; y += 1) {
      const key = getBucketKey(x, y);
      const bucket = spatialIndex.get(key);
      if (bucket) {
        bucket.push(entry);
      } else {
        spatialIndex.set(key, [entry]);
      }
    }
  }
}

function getPlacementOffsets(region: RegionSummary, locale: string): Array<[number, number]> {
  const metrics = getRegionTextMetrics(region.type, locale);
  const compact = usesCompactMapLabels(locale);
  const stepX = compact ? Math.round(metrics.fontSize * 1.9) : Math.round(metrics.fontSize * 2.8);
  const stepY = compact ? Math.round(metrics.lineHeight * 1.25) : Math.round(metrics.lineHeight * 1.2);

  return [
    [0, 0],
    [0, stepY],
    [0, -stepY],
    [stepX, 0],
    [-stepX, 0],
    [stepX, stepY],
    [-stepX, stepY],
    [stepX, -stepY],
    [-stepX, -stepY],
    [0, stepY * 2],
    [0, -stepY * 2],
    [stepX * 2, 0],
    [-stepX * 2, 0],
    [stepX, stepY * 2],
    [-stepX, stepY * 2],
    [stepX, -stepY * 2],
    [-stepX, -stepY * 2],
    [stepX * 2, stepY],
    [stepX * 2, -stepY],
    [-stepX * 2, stepY],
    [-stepX * 2, -stepY],
    [stepX * 2, stepY * 2],
    [-stepX * 2, stepY * 2],
    [stepX * 2, -stepY * 2],
    [-stepX * 2, -stepY * 2],
    [0, stepY * 3],
    [0, -stepY * 3],
    [stepX * 3, 0],
    [-stepX * 3, 0]
  ];
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

  const accepted: AcceptedLabel[] = [];
  const spatialIndex = new Map<string, AcceptedLabel[]>();

  for (const region of sortedRegions) {
    const displayName = formatRegionDisplayName(region.name, locale);
    const placements = getPlacementOffsets(region, locale)
      .map(([offsetX, offsetY]) => estimateLabelPlacement(region, displayName, locale, offsetX, offsetY));

    const chosenPlacement =
      placements.find((placement) => !findCollision(placement.bounds, spatialIndex)) ?? placements[0];

    const entry: AcceptedLabel = {
      label: {
        ...region,
        displayName,
        labelX: chosenPlacement.labelX,
        labelY: chosenPlacement.labelY,
        priority: getRegionPriority(region)
      },
      bounds: chosenPlacement.bounds
    };

    accepted.push(entry);
    addToSpatialIndex(entry, spatialIndex);
  }

  return accepted.map((entry) => entry.label);
}
