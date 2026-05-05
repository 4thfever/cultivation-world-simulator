import { defineComponent, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { avatarApi } from '@/api'
import { useAvatarAdjustmentPanel, type AvatarAdjustmentPanelProps } from '@/composables/useAvatarAdjustmentPanel'
import { RACE_OPTIONS, useCreateAvatarPanel } from '@/composables/useCreateAvatarPanel'
import { useDeleteAvatarPanel } from '@/composables/useDeleteAvatarPanel'

const messageMock = {
  success: vi.fn(),
  error: vi.fn(),
}

vi.mock('naive-ui', () => ({
  useMessage: () => messageMock,
}))

const fetchStateMock = vi.fn()
vi.mock('@/stores/world', () => ({
  useWorldStore: () => ({
    fetchState: fetchStateMock,
  }),
}))

vi.mock('@/api', () => ({
  avatarApi: {
    fetchAvatarAdjustOptions: vi.fn(),
    updateAvatarAdjustment: vi.fn(),
    generateCustomContent: vi.fn(),
    createCustomContent: vi.fn(),
    fetchGameData: vi.fn(),
    fetchAvatarMeta: vi.fn(),
    fetchAvatarList: vi.fn(),
    createAvatar: vi.fn(),
    deleteAvatar: vi.fn(),
  },
}))

const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  messages: {
    'zh-CN': {
      common: {
        none: '无',
      },
      realms: {
        QI_REFINEMENT: '炼气',
        FOUNDATION_ESTABLISHMENT: '筑基',
        CORE_FORMATION: '金丹',
        NASCENT_SOUL: '元婴',
      },
      attributes: {
        FIRE: '火',
      },
      technique_grades: {
        high: '上品',
      },
      game: {
        info_panel: {
          popup: {
            types: {
              sword: '剑',
            },
          },
          avatar: {
            adjust: {
              title: '调整{category}',
              current: '当前',
              select: '选择',
              search_placeholder: '搜索',
              load_failed: '加载失败',
              apply_success: '应用成功',
              apply_failed: '应用失败',
              apply_personas: '应用人格',
              categories: {
                technique: '功法',
                weapon: '武器',
                auxiliary: '辅修',
                personas: '人格',
                goldfinger: '金手指',
              },
              custom: {
                title: '自定义',
                unnamed: '未命名',
                prompt_required: '请输入提示',
                generate_failed: '生成失败',
                create_failed: '保存失败',
                create_success: '保存成功',
              },
            },
          },
        },
      },
      ui: {
        create_avatar: {
          fetch_failed: '加载失败',
          create_success: '创建成功',
          create_failed: '创建失败 {error}',
          relation_labels: {
            parent: '父母',
            child: '子女',
            sibling: '手足',
            master: '师父',
            disciple: '徒弟',
            lover: '道侣',
            friend: '朋友',
            enemy: '敌人',
          },
        },
        delete_avatar: {
          fetch_failed: '加载失败',
          delete_success: '删除成功',
          delete_failed: '删除失败',
          delete_confirm: '删除{name}？',
        },
      },
    },
  },
})

function mountComposable<T>(factory: () => T): T {
  let result!: T
  mount(defineComponent({
    setup() {
      result = factory()
      return () => null
    },
  }), {
    global: {
      plugins: [i18n],
    },
  })
  return result
}

async function settle() {
  await Promise.resolve()
  await Promise.resolve()
  await nextTick()
}

const adjustCatalog = {
  techniques: [
    { id: '1', name: '火云诀', desc: '灼热', grade: 'high', attribute: 'FIRE' },
  ],
  weapons: [],
  auxiliaries: [],
  personas: [
    { id: '7', name: '沉稳', desc: '冷静' },
    { id: '8', name: '锋锐', desc: '果断' },
  ],
  goldfingers: [],
}

describe('avatar panel composables', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(avatarApi.fetchAvatarAdjustOptions).mockResolvedValue(adjustCatalog)
    vi.mocked(avatarApi.updateAvatarAdjustment).mockResolvedValue({ status: 'ok', message: 'ok' })
    vi.mocked(avatarApi.generateCustomContent).mockResolvedValue({
      status: 'ok',
      draft: {
        id: 'draft',
        category: 'technique',
        name: '自创功法',
        desc: '测试',
        effects: {},
      },
    })
    vi.mocked(avatarApi.createCustomContent).mockResolvedValue({
      status: 'ok',
      item: { id: '9', name: '自创功法', desc: '测试' },
    })
    vi.mocked(avatarApi.fetchGameData).mockResolvedValue({
      sects: [{ id: 1, name: '青云宗', alignment: 'GOOD' }],
      races: [
        { id: 'human', label: '人族' },
        { id: 'fox', label: '狐族' },
      ],
      personas: [{ id: 2, name: '沉稳', desc: '冷静', rarity: 'common' }],
      realms: ['QI_REFINEMENT', 'FOUNDATION_ESTABLISHMENT'],
      techniques: [{ id: 3, name: '火云诀', grade: 'high', attribute: 'FIRE', sect: null }],
      weapons: [{ id: 4, name: '青锋剑', grade: 'high', type: 'sword' }],
      auxiliaries: [{ id: 5, name: '炼丹术', grade: 'high' }],
      alignments: [{ value: 'GOOD', label: '正道' }],
    })
    vi.mocked(avatarApi.fetchAvatarMeta).mockResolvedValue({
      human: { male: [1], female: [2] },
      fox: { male: [3], female: [4] },
    })
    vi.mocked(avatarApi.fetchAvatarList).mockResolvedValue([
      { id: 'a1', name: '李青', sect_name: '青云宗', realm: 'QI_REFINEMENT', gender: '男', age: 18 },
    ])
    vi.mocked(avatarApi.createAvatar).mockResolvedValue({ status: 'ok', message: 'ok', avatar_id: 'new' })
    vi.mocked(avatarApi.deleteAvatar).mockResolvedValue({ status: 'ok', message: 'ok' })
    fetchStateMock.mockResolvedValue(undefined)
  })

  it('loads and applies a single avatar adjustment', async () => {
    const callbacks = { onClose: vi.fn(), onUpdated: vi.fn() }
    const props: AvatarAdjustmentPanelProps = { avatarId: 'a1', category: 'technique' }
    const panel = mountComposable(() => useAvatarAdjustmentPanel(props, callbacks))

    await settle()
    expect(panel.filteredOptions.value.map(option => option.name)).toEqual(['无', '火云诀'])

    await panel.handleSingleSelect(panel.filteredOptions.value[1])
    expect(avatarApi.updateAvatarAdjustment).toHaveBeenCalledWith({
      avatar_id: 'a1',
      category: 'technique',
      target_id: 1,
    })
    expect(callbacks.onUpdated).toHaveBeenCalled()
    expect(callbacks.onClose).toHaveBeenCalled()
  })

  it('syncs and applies persona selections', async () => {
    const props: AvatarAdjustmentPanelProps = {
      avatarId: 'a1',
      category: 'personas',
      currentPersonas: [{ id: '7', name: '沉稳' }],
    }
    const panel = mountComposable(() => useAvatarAdjustmentPanel(props, {
      onClose: vi.fn(),
      onUpdated: vi.fn(),
    }))

    await settle()
    panel.togglePersona(panel.filteredOptions.value[1])
    await panel.applyPersonas()

    expect(avatarApi.updateAvatarAdjustment).toHaveBeenCalledWith({
      avatar_id: 'a1',
      category: 'personas',
      persona_ids: [7, 8],
    })
  })

  it('generates and saves custom adjustment content', async () => {
    const callbacks = { onClose: vi.fn(), onUpdated: vi.fn() }
    const panel = mountComposable(() => useAvatarAdjustmentPanel(
      { avatarId: 'a1', category: 'technique' },
      callbacks,
    ))

    await settle()
    panel.customPrompt.value = '做一个火系功法'
    await panel.generateCustomDraft()
    expect(panel.customDraft.value?.name).toBe('自创功法')

    await panel.saveCustomDraft()
    expect(avatarApi.createCustomContent).toHaveBeenCalled()
    expect(avatarApi.updateAvatarAdjustment).toHaveBeenLastCalledWith({
      avatar_id: 'a1',
      category: 'technique',
      target_id: 9,
    })
  })

  it('loads create avatar metadata and submits with default alignment', async () => {
    const onCreated = vi.fn()
    const panel = mountComposable(() => useCreateAvatarPanel(onCreated))

    await settle()
    expect(panel.realmOptions.value[0]).toEqual({ label: '炼气', value: 1 })
    expect(panel.createForm.value.level).toBe(1)

    panel.createForm.value.surname = '李'
    panel.createForm.value.given_name = '青'
    await panel.handleCreateAvatar()

    expect(avatarApi.createAvatar).toHaveBeenCalledWith(expect.objectContaining({
      surname: '李',
      given_name: '青',
      alignment: 'NEUTRAL',
    }))
    expect(fetchStateMock).toHaveBeenCalled()
    expect(onCreated).toHaveBeenCalled()
  })

  it('does not expose hardcoded Chinese race labels in create avatar options', () => {
    const chinesePattern = /[\u4e00-\u9fff]/

    expect(RACE_OPTIONS.map(option => option.label).filter(label => chinesePattern.test(label))).toEqual([])
  })

  it('uses localized race options from game metadata', async () => {
    const panel = mountComposable(() => useCreateAvatarPanel(vi.fn()))
    await settle()

    expect(panel.raceOptions.value).toEqual([
      { label: '人族', value: 'human' },
      { label: '狐族', value: 'fox' },
    ])
  })

  it('resets selected portrait when gender changes', async () => {
    const panel = mountComposable(() => useCreateAvatarPanel(vi.fn()))
    await settle()

    panel.createForm.value.pic_id = 1
    panel.createForm.value.gender = '女'
    await nextTick()

    expect(panel.createForm.value.pic_id).toBeUndefined()
  })

  it('resets selected portrait and switches library when race changes', async () => {
    const panel = mountComposable(() => useCreateAvatarPanel(vi.fn()))
    await settle()

    expect(panel.availableAvatars.value).toEqual([1])
    panel.createForm.value.pic_id = 1
    panel.createForm.value.race = 'fox'
    await nextTick()

    expect(panel.createForm.value.pic_id).toBeUndefined()
    expect(panel.availableAvatars.value).toEqual([3])
  })

  it('normalizes wrapped avatar metadata before switching race libraries', async () => {
    vi.mocked(avatarApi.fetchAvatarMeta).mockResolvedValueOnce({
      data: {
        human: { male: [1], female: [2] },
        fox: { male: [3, 4], female: [5] },
      },
    })
    const panel = mountComposable(() => useCreateAvatarPanel(vi.fn()))
    await settle()

    panel.createForm.value.race = 'fox'
    await nextTick()

    expect(panel.availableAvatars.value).toEqual([3, 4])
  })

  it('filters and deletes avatars after confirmation', async () => {
    const panel = mountComposable(() => useDeleteAvatarPanel(() => true))
    await settle()

    panel.avatarSearch.value = '李'
    expect(panel.filteredAvatars.value).toHaveLength(1)

    await panel.handleDeleteAvatar('a1', '李青')
    expect(avatarApi.deleteAvatar).toHaveBeenCalledWith('a1')
    expect(fetchStateMock).toHaveBeenCalled()
  })

  it('does not delete when confirmation is cancelled', async () => {
    const panel = mountComposable(() => useDeleteAvatarPanel(() => false))
    await settle()

    await panel.handleDeleteAvatar('a1', '李青')
    expect(avatarApi.deleteAvatar).not.toHaveBeenCalled()
  })
})
