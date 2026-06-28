import type { EffectEntity } from '@/types/core';

const iconModules = import.meta.glob('@/assets/icons/items/*.png', {
  eager: true,
  query: '?url',
  import: 'default',
}) as Record<string, string>;

const itemIconUrls = new Map<string, string>();

for (const [path, url] of Object.entries(iconModules)) {
  const filename = path.split('/').pop()?.replace(/\.png$/, '');
  if (filename) {
    itemIconUrls.set(filename, url);
  }
}

const ITEM_CATEGORIES = ['weapon', 'elixir', 'auxiliary', 'technique', 'goldfinger', 'animal', 'plant', 'lode', 'material'] as const;
type ItemIconCategory = (typeof ITEM_CATEGORIES)[number];

function normalizeId(value: unknown): string {
  return String(value ?? '').trim();
}

function hasIcon(key: string): boolean {
  return itemIconUrls.has(key);
}

function getIcon(key: string): string | undefined {
  return itemIconUrls.get(key);
}

function inferCategory(item: Partial<EffectEntity> | undefined | null): ItemIconCategory | undefined {
  if (!item) return undefined;
  const rawType = String(item.type ?? '').toLowerCase();
  const rawTypeName = String(item.type_name ?? '').toLowerCase();
  const rawKey = String(item.key ?? '').trim();
  const id = normalizeId(item.id);

  if (rawType === 'technique') return 'technique';
  if (rawType === 'elixir') return 'elixir';
  if (rawType === 'auxiliary') return 'auxiliary';
  if (rawType === 'animal') return 'animal';
  if (rawType === 'plant') return 'plant';
  if (rawType === 'lode') return 'lode';
  if (rawType === 'material') return 'material';
  if (item.icon_category && ITEM_CATEGORIES.includes(item.icon_category as ItemIconCategory)) {
    return item.icon_category as ItemIconCategory;
  }
  if (rawType === 'goldfinger') return 'goldfinger';
  if (rawKey && item.rarity && !rawType) return 'goldfinger';
  if (rawKey && hasIcon(`goldfinger_${id}`)) return 'goldfinger';
  if (item.rarity && hasIcon(`goldfinger_${id}`)) return 'goldfinger';
  if (rawTypeName.includes('丹') || rawTypeName.includes('elixir')) return 'elixir';
  if (rawTypeName.includes('功法') || rawTypeName.includes('technique')) return 'technique';
  if (rawTypeName.includes('外挂') || rawTypeName.includes('goldfinger')) return 'goldfinger';
  if (rawTypeName.includes('动物') || rawTypeName.includes('灵兽') || rawTypeName.includes('animal')) return 'animal';
  if (rawTypeName.includes('植物') || rawTypeName.includes('灵植') || rawTypeName.includes('plant')) return 'plant';
  if (rawTypeName.includes('矿') || rawTypeName.includes('lode')) return 'lode';
  if (rawTypeName.includes('材料') || rawTypeName.includes('material')) return 'material';
  if (hasIcon(`weapon_${id}`)) return 'weapon';
  if (hasIcon(`elixir_${id}`)) return 'elixir';
  if (hasIcon(`auxiliary_${id}`)) return 'auxiliary';
  if (hasIcon(`technique_${id}`)) return 'technique';
  if (hasIcon(`goldfinger_${id}`)) return 'goldfinger';
  if (hasIcon(`animal_${id}`)) return 'animal';
  if (hasIcon(`plant_${id}`)) return 'plant';
  if (hasIcon(`lode_${id}`)) return 'lode';
  if (hasIcon(`material_${id}`)) return 'material';
  return undefined;
}

function candidateKeys(item: Partial<EffectEntity> | undefined | null): string[] {
  if (!item) return [];
  const id = normalizeId(item.id);
  if (!id) return [];
  const category = inferCategory(item);
  const keys: string[] = [];
  if (category) keys.push(`${category}_${id}`);
  for (const fallbackCategory of ITEM_CATEGORIES) {
    keys.push(`${fallbackCategory}_${id}`);
  }
  return [...new Set(keys)];
}

export function getItemIconUrl(item: Partial<EffectEntity> | undefined | null): string | undefined {
  for (const key of candidateKeys(item)) {
    const url = getIcon(key);
    if (url) return url;
  }
  const category = inferCategory(item);
  return getIcon(category ? `fallback_${category}` : 'fallback_unknown');
}

export function hasItemIcon(item: Partial<EffectEntity> | undefined | null): boolean {
  return Boolean(getItemIconUrl(item));
}
