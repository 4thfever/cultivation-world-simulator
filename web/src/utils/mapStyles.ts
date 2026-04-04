import type { TextStyleOptions } from 'pixi.js';

type RegionTextMetrics = {
  fontSize: number;
  lineHeight: number;
  strokeWidth: number;
};

const COMPACT_SCRIPT_FONT_SCALE = {
  sect: 64,
  city: 70,
  default: 68
} as const;

const LATIN_FONT_SCALE = {
  sect: 64,
  city: 70,
  default: 68
} as const;

export function usesCompactMapLabels(locale: string): boolean {
  return locale.startsWith('zh') || locale.startsWith('ja');
}

export function getRegionTextMetrics(type: string, locale: string): RegionTextMetrics {
  const compact = usesCompactMapLabels(locale);
  const scale = compact ? COMPACT_SCRIPT_FONT_SCALE : LATIN_FONT_SCALE;
  const baseFontSize = scale[type as keyof typeof scale] ?? scale.default;

  return {
    fontSize: baseFontSize,
    lineHeight: Math.round(baseFontSize * (compact ? 1.06 : 1.1)),
    strokeWidth: compact ? 5 : 4
  };
}

// 地图渲染相关的样式常量
export function getRegionTextStyle(type: string, locale = 'zh-CN'): Partial<TextStyleOptions> {
  const metrics = getRegionTextMetrics(type, locale);
  const compact = usesCompactMapLabels(locale);

  const styleByType: Record<string, Partial<TextStyleOptions>> = {
    sect: {
      fill: '#ffcc00'
    },
    city: {
      fill: '#ccffcc'
    },
    default: {
      fill: '#ffffff'
    }
  };

  return {
    fontFamily: '"Microsoft YaHei", sans-serif',
    fontSize: metrics.fontSize,
    lineHeight: metrics.lineHeight,
    fill: (styleByType[type] || styleByType.default).fill,
    stroke: { color: '#000000', width: metrics.strokeWidth, join: 'round' },
    align: 'center',
    whiteSpace: 'pre',
    dropShadow: {
      color: '#000000',
      blur: compact ? 3 : 2,
      angle: Math.PI / 6,
      distance: compact ? 3 : 2,
      alpha: 0.8
    }
  };
}

