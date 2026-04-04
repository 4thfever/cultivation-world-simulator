import type { ComposerTranslation } from 'vue-i18n';

export function formatPopulationValue(value: number | undefined): string {
  return (value ?? 0).toFixed(1);
}

export function formatPopulationText(
  value: number | undefined,
  t: ComposerTranslation
): string {
  return t('game.mortal_system.population_value', {
    value: formatPopulationValue(value)
  });
}

export function formatPopulationGrowthText(
  value: number | undefined,
  t: ComposerTranslation
): string {
  const normalized = value ?? 0;
  const prefix = normalized > 0 ? '+' : '';

  return t('game.mortal_system.population_growth_value', {
    value: `${prefix}${normalized.toFixed(2)}`
  });
}

export function formatPopulationRatioText(
  current: number | undefined,
  capacity: number | undefined,
  t: ComposerTranslation
): string {
  return t('game.mortal_system.population_ratio_value', {
    current: formatPopulationValue(current),
    capacity: formatPopulationValue(capacity)
  });
}
