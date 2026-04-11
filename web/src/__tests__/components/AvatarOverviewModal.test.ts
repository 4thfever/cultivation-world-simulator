import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'

const mocks = vi.hoisted(() => ({
  refreshOverviewMock: vi.fn(),
  fetchDeceasedListMock: vi.fn(),
  fetchEventsMock: vi.fn(),
}))

let mockOverview: any = {
  summary: {
    totalCount: 12,
    aliveCount: 9,
    deadCount: 3,
    sectMemberCount: 7,
    rogueCount: 2,
  },
  realmDistribution: [{ realm: '练气', count: 6 }],
}
let mockOverviewLoading = false

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      if (!params) return key
      return `${key}:${JSON.stringify(params)}`
    },
  }),
}))

vi.mock('@/stores/avatarOverview', () => ({
  useAvatarOverviewStore: () => ({
    get overview() { return mockOverview },
    get isLoading() { return mockOverviewLoading },
    refreshOverview: mocks.refreshOverviewMock,
  }),
}))

vi.mock('@/api/modules/world', () => ({
  worldApi: {
    fetchDeceasedList: mocks.fetchDeceasedListMock,
  },
}))

vi.mock('@/api/modules/event', () => ({
  eventApi: {
    fetchEvents: mocks.fetchEventsMock,
  },
}))

vi.mock('@/utils/cultivationText', () => ({
  formatRealmStage: (realm: string, stage: string) => `${realm}-${stage}`,
}))

const NModalStub = defineComponent({
  name: 'NModal',
  props: ['show', 'title', 'preset'],
  emits: ['update:show'],
  setup(props, { slots }) {
    return () => props.show ? h('div', { class: 'n-modal-stub' }, slots.default?.()) : null
  },
})

const NTabsStub = defineComponent({
  name: 'NTabs',
  props: ['value'],
  emits: ['update:value'],
  setup(props, { slots }) {
    return () => h('div', { class: 'n-tabs-stub', 'data-value': props.value }, slots.default?.())
  },
})

const NTabPaneStub = defineComponent({
  name: 'NTabPane',
  props: ['name', 'tab'],
  setup(_, { slots }) {
    return () => h('div', { class: 'n-tab-pane-stub' }, slots.default?.())
  },
})

const NTableStub = defineComponent({
  name: 'NTable',
  setup(_, { slots }) {
    return () => h('table', { class: 'n-table-stub' }, slots.default?.())
  },
})

const NSpinStub = defineComponent({
  name: 'NSpin',
  props: ['show'],
  setup(_, { slots }) {
    return () => h('div', { class: 'n-spin-stub' }, slots.default?.())
  },
})

const NEmptyStub = defineComponent({
  name: 'NEmpty',
  props: ['description'],
  setup(props) {
    return () => h('div', { class: 'n-empty-stub' }, props.description)
  },
})

const NButtonStub = defineComponent({
  name: 'NButton',
  emits: ['click'],
  setup(_, { slots, emit }) {
    return () => h('button', { class: 'n-button-stub', onClick: () => emit('click') }, slots.default?.())
  },
})

import AvatarOverviewModal from '@/components/game/panels/AvatarOverviewModal.vue'

describe('AvatarOverviewModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockOverview = {
      summary: {
        totalCount: 12,
        aliveCount: 9,
        deadCount: 3,
        sectMemberCount: 7,
        rogueCount: 2,
      },
      realmDistribution: [{ realm: '练气', count: 6 }],
    }
    mockOverviewLoading = false
    mocks.fetchDeceasedListMock.mockResolvedValue([
      {
        id: 'dead-1',
        name: '陨落者',
        gender: '男',
        age_at_death: 88,
        realm_at_death: '金丹',
        stage_at_death: '前期',
        death_reason: '战死',
        death_time: 35,
        sect_name_at_death: '青云宗',
        alignment_at_death: '正道',
        backstory: '往事',
        custom_pic_id: null,
      },
    ])
    mocks.fetchEventsMock.mockResolvedValue({
      events: [
        { id: 'evt-1', year: 3, month: 4, content: '陨落之战' },
      ],
    })
  })

  const globalConfig = {
    global: {
      stubs: {
        NModal: NModalStub,
        NTabs: NTabsStub,
        NTabPane: NTabPaneStub,
        NTable: NTableStub,
        NSpin: NSpinStub,
        NEmpty: NEmptyStub,
        NButton: NButtonStub,
      },
    },
  }

  it('refreshes overview when shown', async () => {
    mount(AvatarOverviewModal, {
      ...globalConfig,
      props: { show: true },
    })

    await nextTick()
    expect(mocks.refreshOverviewMock).toHaveBeenCalled()
  })
})
