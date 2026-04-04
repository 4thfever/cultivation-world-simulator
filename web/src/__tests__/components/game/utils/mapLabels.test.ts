import { describe, expect, it } from 'vitest';
import { buildVisibleRegionLabels, formatRegionDisplayName } from '@/components/game/utils/mapLabels';
import type { RegionSummary } from '@/types/core';

function createRegion(overrides: Partial<RegionSummary>): RegionSummary {
  return {
    id: String(overrides.id ?? '1'),
    name: overrides.name ?? 'Test Region',
    type: overrides.type ?? 'normal',
    x: overrides.x ?? 0,
    y: overrides.y ?? 0,
    sect_id: overrides.sect_id,
    sect_name: overrides.sect_name,
    sect_color: overrides.sect_color,
    sect_is_active: overrides.sect_is_active,
    sub_type: overrides.sub_type
  };
}

describe('mapLabels', () => {
  it('wraps English map labels into at most two lines', () => {
    expect(formatRegionDisplayName('Purple Bamboo Secluded Realm', 'en-US')).toBe(
      'Purple Bamboo\nSecluded Realm'
    );
  });

  it('keeps Chinese labels on a single line', () => {
    expect(formatRegionDisplayName('紫竹幽境', 'zh-CN')).toBe('紫竹幽境');
  });

  it('avoids overlaps by moving lower-priority labels', () => {
    const labels = buildVisibleRegionLabels(
      [
        createRegion({ id: 'normal', type: 'normal', name: 'Purple Bamboo Secluded Realm', x: 10, y: 10 }),
        createRegion({ id: 'city', type: 'city', name: 'Qingyun City', x: 10, y: 10 })
      ],
      'en-US'
    );

    expect(labels).toHaveLength(2);
    expect(labels.map((label) => label.id)).toEqual(['city', 'normal']);
    expect(labels[0]?.labelX).toBe((10 * 64) + (64 / 2));
    expect(labels[0]?.labelY).toBe((10 * 64) + (64 * 1.5));
    expect(
      labels[1]?.labelX !== labels[0]?.labelX || labels[1]?.labelY !== labels[0]?.labelY
    ).toBe(true);
  });

  it('keeps separated labels visible', () => {
    const labels = buildVisibleRegionLabels(
      [
        createRegion({ id: 'a', type: 'city', name: 'Qingyun City', x: 2, y: 2 }),
        createRegion({ id: 'b', type: 'sect', name: 'Echo Valley', x: 12, y: 8 })
      ],
      'en-US'
    );

    expect(labels.map((label) => label.id)).toEqual(['a', 'b']);
  });

  it('moves long English labels before allowing overlap', () => {
    const labels = buildVisibleRegionLabels(
      [
        createRegion({ id: '414', type: 'sect', name: 'Asura Blood Pool', x: 10, y: 22 }),
        createRegion({ id: '102', type: 'normal', name: 'Western Quicksand', x: 4, y: 23 })
      ],
      'en-US'
    );

    expect(labels.map((label) => label.id)).toEqual(['414', '102']);
    expect(labels[1]?.labelX).toBe((4 * 64) + (64 / 2));
    expect(labels[1]?.labelY).not.toBe((23 * 64) + (64 * 1.5));
  });

  it('also avoids overlap for compact-script locales', () => {
    const labels = buildVisibleRegionLabels(
      [
        createRegion({ id: 'a', type: 'sect', name: '修罗血池', x: 10, y: 22 }),
        createRegion({ id: 'b', type: 'normal', name: '西域流沙', x: 10, y: 22 })
      ],
      'ja-JP'
    );

    expect(labels).toHaveLength(2);
    expect(labels.map((label) => label.id)).toEqual(['a', 'b']);
    expect(
      labels[1]?.labelX !== labels[0]?.labelX || labels[1]?.labelY !== labels[0]?.labelY
    ).toBe(true);
  });
});
