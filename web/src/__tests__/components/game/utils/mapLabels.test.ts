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

  it('hides lower-priority labels when they collide', () => {
    const labels = buildVisibleRegionLabels(
      [
        createRegion({ id: 'normal', type: 'normal', name: 'Purple Bamboo Secluded Realm', x: 10, y: 10 }),
        createRegion({ id: 'city', type: 'city', name: 'Qingyun City', x: 10, y: 10 })
      ],
      'en-US'
    );

    expect(labels).toHaveLength(1);
    expect(labels[0]?.id).toBe('city');
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
});
