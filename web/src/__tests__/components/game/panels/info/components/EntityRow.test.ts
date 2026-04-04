import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { createI18n } from 'vue-i18n'
import EntityRow from '@/components/game/panels/info/components/EntityRow.vue'

function buildI18n(locale: string) {
  return createI18n({
    legacy: false,
    locale,
    messages: {
      'zh-CN': {
        technique_grades: {
          MIDDLE: '中品',
        },
      },
      'en-US': {
        technique_grades: {
          MIDDLE: 'Mid Grade',
        },
      },
      'vi-VN': {
        technique_grades: {
          MIDDLE: 'Phẩm trung',
        },
      },
      'ja-JP': {
        technique_grades: {
          MIDDLE: '中品',
        },
      },
    },
  })
}

describe('EntityRow', () => {
  const baseItem = {
    name: '金光罩',
    grade: 'MIDDLE',
  }

  it('prefers inline details for Chinese and Japanese', () => {
    for (const locale of ['zh-CN', 'ja-JP']) {
      const wrapper = mount(EntityRow, {
        props: {
          item: baseItem as any,
          meta: '熟练度 0.0%',
          detailsBelow: true,
        },
        global: {
          plugins: [buildI18n(locale)],
          directives: {
            sound: () => {},
          },
        },
      })

      expect(wrapper.classes()).toContain('details-inline-preferred')
      expect(wrapper.find('.inline-info').exists()).toBe(true)
      expect(wrapper.find('.details-line').exists()).toBe(false)
    }
  })

  it('keeps stacked details for English and Vietnamese', () => {
    for (const locale of ['en-US', 'vi-VN']) {
      const wrapper = mount(EntityRow, {
        props: {
          item: baseItem as any,
          meta: 'Proficiency 0.0%',
          detailsBelow: true,
        },
        global: {
          plugins: [buildI18n(locale)],
          directives: {
            sound: () => {},
          },
        },
      })

      expect(wrapper.classes()).toContain('details-stacked')
      expect(wrapper.find('.inline-info').exists()).toBe(false)
      expect(wrapper.find('.details-line').exists()).toBe(true)
    }
  })
})
