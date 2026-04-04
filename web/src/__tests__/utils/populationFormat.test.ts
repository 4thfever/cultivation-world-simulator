import { describe, expect, it } from 'vitest'
import { createI18n } from 'vue-i18n'

import {
  formatPopulationGrowthText,
  formatPopulationRatioText,
  formatPopulationText,
  formatPopulationValue,
} from '@/utils/populationFormat'

function createTranslator(locale: string) {
  const mortalSystemMessages =
    locale === 'zh-CN'
      ? {
          population_value: '{value} 万',
          population_growth_value: '{value} 万/月',
          population_ratio_value: '{current} / {capacity} 万',
        }
      : locale === 'ja-JP'
        ? {
            population_value: '{value}万',
            population_growth_value: '{value}万/月',
            population_ratio_value: '{current} / {capacity}万',
          }
        : locale === 'vi-VN'
          ? {
              population_value: '{value}',
              population_growth_value: '{value}/tháng',
              population_ratio_value: '{current} / {capacity}',
            }
          : {
              population_value: '{value}',
              population_growth_value: '{value}/month',
              population_ratio_value: '{current} / {capacity}',
            }

  const i18n = createI18n({
    legacy: false,
    locale,
    messages: {
      [locale]: {
        game: {
          mortal_system: mortalSystemMessages,
        },
      },
    },
  })

  return i18n.global.t
}

describe('populationFormat', () => {
  it('keeps Chinese-style myriad units for zh-CN', () => {
    const t = createTranslator('zh-CN')

    expect(formatPopulationValue(831.1, 'zh-CN')).toBe('831.1')
    expect(formatPopulationText(831.1, t, 'zh-CN')).toBe('831.1 万')
    expect(formatPopulationGrowthText(3.23, t, 'zh-CN')).toBe('+3.23 万/月')
  })

  it('formats English population with compact western units', () => {
    const t = createTranslator('en-US')

    expect(formatPopulationText(831.1, t, 'en-US')).toBe('8.31M')
    expect(formatPopulationGrowthText(3.23, t, 'en-US')).toBe('+32.3K/month')
    expect(formatPopulationRatioText(831.1, 955.0, t, 'en-US')).toBe('8.31M / 9.55M')
  })

  it('formats Vietnamese population with readable long compact units', () => {
    const t = createTranslator('vi-VN')

    expect(formatPopulationText(831.1, t, 'vi-VN')).toBe('8,31 triệu')
    expect(formatPopulationGrowthText(3.23, t, 'vi-VN')).toBe('+32,3 nghìn/tháng')
    expect(formatPopulationRatioText(831.1, 955.0, t, 'vi-VN')).toBe('8,31 triệu / 9,55 triệu')
  })

  it('keeps myriad units for Japanese', () => {
    const t = createTranslator('ja-JP')

    expect(formatPopulationText(831.1, t, 'ja-JP')).toBe('831.1万')
    expect(formatPopulationGrowthText(3.23, t, 'ja-JP')).toBe('+3.23万/月')
  })
})
