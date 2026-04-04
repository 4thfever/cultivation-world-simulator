import type { ComposerTranslation } from 'vue-i18n';

const MYRIAD_LOCALES = new Set(['zh-CN', 'zh-TW', 'ja-JP']);

function normalizeLocale(locale: string | undefined): string {
  return locale || 'en-US';
}

function formatCompactNumber(
  value: number,
  locale: string,
  options?: Intl.NumberFormatOptions,
): string {
  return new Intl.NumberFormat(locale, {
    notation: 'compact',
    ...options,
  }).format(value);
}

export function formatPopulationValue(
  value: number | undefined,
  locale?: string,
): string {
  const normalized = value ?? 0;
  const resolvedLocale = normalizeLocale(locale);

  if (MYRIAD_LOCALES.has(resolvedLocale)) {
    return normalized.toFixed(1);
  }

  const actualPopulation = normalized * 10000;

  if (resolvedLocale === 'vi-VN') {
    return formatCompactNumber(actualPopulation, resolvedLocale, {
      compactDisplay: 'long',
      maximumFractionDigits: 2,
    });
  }

  return formatCompactNumber(actualPopulation, resolvedLocale, {
    maximumFractionDigits: 2,
  });
}

export function formatPopulationText(
  value: number | undefined,
  t: ComposerTranslation,
  locale?: string,
): string {
  return t('game.mortal_system.population_value', {
    value: formatPopulationValue(value, locale)
  });
}

export function formatPopulationGrowthText(
  value: number | undefined,
  t: ComposerTranslation,
  locale?: string,
): string {
  const normalized = value ?? 0;
  const prefix = normalized > 0 ? '+' : '';
  const resolvedLocale = normalizeLocale(locale);

  if (MYRIAD_LOCALES.has(resolvedLocale)) {
    return t('game.mortal_system.population_growth_value', {
      value: `${prefix}${normalized.toFixed(2)}`
    });
  }

  const actualGrowth = normalized * 10000;
  const formattedValue =
    resolvedLocale === 'vi-VN'
      ? formatCompactNumber(actualGrowth, resolvedLocale, {
          compactDisplay: 'long',
          maximumFractionDigits: 1,
        })
      : formatCompactNumber(actualGrowth, resolvedLocale, {
          maximumFractionDigits: 1,
        });

  return t('game.mortal_system.population_growth_value', {
    value: `${prefix}${formattedValue}`
  });
}

export function formatPopulationRatioText(
  current: number | undefined,
  capacity: number | undefined,
  t: ComposerTranslation,
  locale?: string,
): string {
  return t('game.mortal_system.population_ratio_value', {
    current: formatPopulationValue(current, locale),
    capacity: formatPopulationValue(capacity, locale)
  });
}
