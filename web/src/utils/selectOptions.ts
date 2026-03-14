export interface SelectOptionLike<TValue extends string | number = string | number> {
  label: string
  value: TValue
}

/**
 * 为下拉选项列表前置一个“全部”选项。
 * 当 i18n key 未命中时，回退到显式提供的 fallback，避免界面直接显示 key。
 */
export function prependAllOption<TValue extends string | number>(
  options: SelectOptionLike<TValue>[],
  allLabel: string,
  translationKey: string,
  fallbackLabel: string,
  allValue: string | number
): Array<SelectOptionLike<TValue | string | number>> {
  const finalLabel = !allLabel || allLabel === translationKey ? fallbackLabel : allLabel

  return [
    { label: finalLabel, value: allValue },
    ...options,
  ]
}
