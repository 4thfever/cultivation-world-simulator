import type { TextStyleOptions } from 'pixi.js';

// 地图渲染相关的样式常量

export const REGION_STYLES: Record<string, Partial<TextStyleOptions>> = {
  sect: {
    fontFamily: '"Microsoft YaHei", sans-serif',
    fontSize: 60,
    fill: '#ffcc00',
    stroke: { color: '#000000', width: 5, join: 'round' },
    align: 'center',
    dropShadow: {
      color: '#000000',
      blur: 3,
      angle: Math.PI / 6,
      distance: 3,
      alpha: 0.8
    }
  },
  city: {
    fontFamily: '"Microsoft YaHei", sans-serif',
    fontSize: 72,
    fill: '#ccffcc',
    stroke: { color: '#000000', width: 5, join: 'round' },
    align: 'center',
    dropShadow: {
      color: '#000000',
      blur: 3,
      angle: Math.PI / 6,
      distance: 3,
      alpha: 0.8
    }
  },
  default: {
    fontFamily: '"Microsoft YaHei", sans-serif',
    fontSize: 72,
    fill: '#ffffff',
    stroke: { color: '#000000', width: 5, join: 'round' },
    align: 'center',
    dropShadow: {
      color: '#000000',
      blur: 3,
      angle: Math.PI / 6,
      distance: 3,
      alpha: 0.8
    }
  }
};

export function getRegionTextStyle(type: string): Partial<TextStyleOptions> {
  return REGION_STYLES[type] || REGION_STYLES.default;
}

