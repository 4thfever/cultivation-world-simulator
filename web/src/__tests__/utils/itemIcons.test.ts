import { describe, expect, it } from 'vitest';
import { getItemIconUrl, hasItemIcon } from '@/utils/itemIcons';

describe('itemIcons', () => {
  it('resolves concrete item icons by inferred category and id', () => {
    expect(getItemIconUrl({ id: '1001', name: '练气剑', type: 'SWORD' })).toContain('weapon_1001');
    expect(getItemIconUrl({ id: '3001', name: '练气破境丹', type: 'elixir' })).toContain('elixir_3001');
    expect(getItemIconUrl({ id: '1', name: '混元金身', type: 'technique' })).toContain('technique_1');
    expect(getItemIconUrl({ id: '1', name: '气运之子', key: 'CHILD_OF_FORTUNE', rarity: 'SSR' })).toContain('goldfinger_1');
    expect(getItemIconUrl({ id: '1', name: '灵兔', type: 'animal' })).toContain('animal_1');
    expect(getItemIconUrl({ id: '1', name: '奇草', type: 'plant' })).toContain('plant_1');
    expect(getItemIconUrl({ id: '1', name: '玄铁矿脉', type: 'lode' })).toContain('lode_1');
    expect(getItemIconUrl({ id: '1', name: '灵兔毛', type: 'material' })).toContain('material_1');
  });

  it('falls back to category icons for custom content', () => {
    expect(getItemIconUrl({ id: '900001', name: '自创功法', type: 'technique', is_custom: true })).toContain('fallback_technique');
    expect(getItemIconUrl({ id: '930001', name: '自定义外挂', key: 'CUSTOM', rarity: 'SSR', is_custom: true })).toContain('fallback_goldfinger');
  });

  it('returns an unknown fallback for non-item entities', () => {
    expect(getItemIconUrl({ id: 'unknown', name: '未知实体' })).toContain('fallback_unknown');
    expect(hasItemIcon({ id: 'unknown', name: '未知实体' })).toBe(true);
  });
});
