import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import DynastyOverviewModal from '@/components/game/panels/DynastyOverviewModal.vue'

const refreshOverviewMock = vi.fn()

vi.mock('naive-ui', () => ({
  NModal: {
    name: 'NModal',
    template: '<div v-if="show" class="n-modal"><slot /></div>',
    props: ['show', 'title', 'preset'],
  },
  NTag: {
    name: 'NTag',
    template: '<span class="n-tag"><slot /></span>',
    props: ['bordered', 'type', 'size'],
  },
  NSpin: {
    name: 'NSpin',
    template: '<div class="n-spin"><slot /></div>',
    props: ['show'],
  },
}))

vi.mock('@/stores/dynasty', () => ({
  useDynastyStore: () => ({
    overview: {
      name: '晋',
      title: '晋朝',
      royal_surname: '司马',
      royal_house_name: '司马氏',
      desc: '门第森然，士族清谈，朝野重礼而尚名教。',
      effect_desc: '',
      is_low_magic: true,
      current_emperor: {
        name: '司马承安',
        surname: '司马',
        given_name: '承安',
        age: 34,
        max_age: 67,
        is_mortal: true,
      },
    },
    isLoading: false,
    isLoaded: true,
    refreshOverview: refreshOverviewMock,
  }),
}))

describe('DynastyOverviewModal', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  function createWrapper(show = true) {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {
        'zh-CN': {
          game: {
            dynasty: {
              title: '王朝',
              name: '王朝名',
              royal_house: '皇族',
              effect: '王朝效果',
              effect_empty: '当前暂无王朝效果。待官职系统与后续逻辑接入后补充。',
              low_magic: '凡人王朝',
              empty: '暂无王朝数据',
              emperor: {
                title: '当朝皇帝',
                name: '姓名',
                age: '年龄',
                lifespan: '寿元',
                identity: '身份',
                mortal: '凡人',
                empty: '暂无皇帝数据',
              },
              summary: {
                title: '王朝概览',
              },
            },
          },
        },
      },
    })

    return mount(DynastyOverviewModal, {
      props: { show },
      global: {
        plugins: [i18n],
      },
    })
  }

  it('fetches overview when opened', async () => {
    const wrapper = createWrapper(false)
    await wrapper.setProps({ show: true })
    expect(refreshOverviewMock).toHaveBeenCalled()
  })

  it('renders dynasty summary', () => {
    const wrapper = createWrapper(true)
    const text = wrapper.text()
    expect(text).toContain('晋朝')
    expect(text).toContain('司马氏')
    expect(text).toContain('司马承安')
    expect(text).toContain('34')
    expect(text).toContain('67')
    expect(text).toContain('门第森然')
    expect(text).toContain('凡人王朝')
    expect(text).toContain('当前暂无王朝效果')
  })
})
