export type EntityRowDetailLayout = 'inline-preferred' | 'stacked';

const ENTITY_ROW_DETAIL_LAYOUT_BY_LOCALE: Record<string, EntityRowDetailLayout> = {
  'zh-CN': 'inline-preferred',
  'zh-TW': 'inline-preferred',
  'ja-JP': 'inline-preferred',
  'en-US': 'stacked',
  'vi-VN': 'stacked',
};

const ENTITY_ROW_DETAIL_LAYOUT_BY_PREFIX: Record<string, EntityRowDetailLayout> = {
  zh: 'inline-preferred',
  ja: 'inline-preferred',
  en: 'stacked',
  vi: 'stacked',
};

export function getEntityRowDetailLayout(locale: string | undefined): EntityRowDetailLayout {
  const normalizedLocale = (locale || 'en-US').trim();
  if (!normalizedLocale) return 'stacked';

  const explicitMatch = ENTITY_ROW_DETAIL_LAYOUT_BY_LOCALE[normalizedLocale];
  if (explicitMatch) {
    return explicitMatch;
  }

  const prefix = normalizedLocale.split('-')[0]?.toLowerCase();
  if (prefix && ENTITY_ROW_DETAIL_LAYOUT_BY_PREFIX[prefix]) {
    return ENTITY_ROW_DETAIL_LAYOUT_BY_PREFIX[prefix];
  }

  return 'stacked';
}
