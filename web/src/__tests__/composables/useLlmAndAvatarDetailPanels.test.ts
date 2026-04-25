import { defineComponent, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { llmApi, avatarApi } from '@/api'
import { useLlmConfigPanel } from '@/composables/useLlmConfigPanel'
import {
  buildAvatarRelationMetaLines,
  parseAvatarEffectLine,
  useAvatarDetailPanel,
} from '@/composables/useAvatarDetailPanel'
import type { AvatarDetail } from '@/types/core'

const messageMock = {
  success: vi.fn(),
  error: vi.fn(),
  warning: vi.fn(),
  info: vi.fn(),
}
const dialogMock = {
  error: vi.fn(),
}

vi.mock('naive-ui', () => ({
  useMessage: () => messageMock,
  useDialog: () => dialogMock,
}))

vi.mock('@/api', () => ({
  llmApi: {
    fetchConfig: vi.fn(),
    testConnection: vi.fn(),
    saveConfig: vi.fn(),
  },
  avatarApi: {
    setLongTermObjective: vi.fn(),
    clearLongTermObjective: vi.fn(),
  },
}))

const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  messages: {
    'zh-CN': {
      common: {
        confirm: '确认',
      },
      ui: {
        other: '其他',
        create_avatar: {
          gender_labels: {
            male: '男',
            female: '女',
          },
        },
      },
      llm: {
        fetch_failed: '加载失败',
        base_url_required: '需要地址',
        test_success: '测试成功',
        save_success: '保存成功',
        test_save_failed_title: '失败',
        preset_applied: '已应用{name}{extra}',
        preset_extra_local: '本地',
        preset_extra_key: '密钥',
        modes: {
          default: '默认',
          default_desc: '默认说明',
          normal: '常规',
          normal_desc: '常规说明',
          fast: '快速',
          fast_desc: '快速说明',
        },
        formats: {
          openai: 'OpenAI',
          openai_desc: 'OpenAI 格式',
          anthropic: 'Anthropic',
          anthropic_desc: 'Anthropic 格式',
        },
        presets: {
          qwen: 'Qwen',
          gemini: 'Gemini',
          openai: 'OpenAI',
          anthropic: 'Anthropic',
          kimi: 'Kimi',
          deepseek: 'DeepSeek',
          groq: 'Groq',
          minimax: 'MiniMax',
          longcat: 'LongCat',
          siliconflow: 'SiliconFlow',
          openrouter: 'OpenRouter',
          ollama: 'Ollama',
        },
      },
      game: {
        ranking: {
          heaven: '天榜',
        },
        info_panel: {
          avatar: {
            weapon_meta: '熟练 {value}',
            stats: {
              rogue: '散修',
            },
            sections: {
              goldfinger: '金手指',
            },
            adjust: {
              categories: {
                technique: '功法',
                weapon: '武器',
                auxiliary: '辅修',
              },
            },
            modals: {
              clear_confirm: '确认清除？',
              set_failed: '设置失败',
            },
          },
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

const avatarData = (): AvatarDetail => ({
  id: 'a1',
  name: '李青',
  realm: 'QI_REFINEMENT',
  pic_id: 1,
  level: 1,
  age: 20,
  lifespan: 100,
  origin: '山村',
  hp: { cur: 10, max: 10 },
  gender: 'Male',
  alignment: 'GOOD',
  root: '金',
  luck: 0,
  magic_stone: 0,
  appearance: '清秀',
  base_battle_strength: 10,
  emotion: { emoji: ':)', name: '平静' },
  is_dead: false,
  current_effects: '[功法] 攻击+1；速度+2\n未标注效果',
  personas: [],
  materials: [],
  relations: [],
  ranking: { type: 'heaven', rank: 2 },
})

describe('useLlmConfigPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(llmApi.fetchConfig).mockResolvedValue({
      base_url: 'https://example.com',
      model_name: 'normal',
      fast_model_name: 'fast',
      mode: 'default',
      max_concurrent_requests: 8,
      has_api_key: true,
      api_format: 'openai',
    })
    vi.mocked(llmApi.testConnection).mockResolvedValue(true)
    vi.mocked(llmApi.saveConfig).mockResolvedValue(true)
  })

  it('loads config, applies local preset, then tests and saves', async () => {
    const onSaved = vi.fn()
    const panel = mountComposable(() => useLlmConfigPanel(onSaved))
    await settle()

    expect(panel.hasSavedApiKey.value).toBe(true)
    expect(panel.config.value.model_name).toBe('normal')

    const ollama = panel.presets.value.find(preset => preset.isLocal)
    expect(ollama).toBeTruthy()
    panel.applyPreset(ollama!)
    expect(panel.config.value.api_key).toBe('ollama')

    await panel.handleTestAndSave()
    expect(llmApi.testConnection).toHaveBeenCalledWith(panel.config.value)
    expect(llmApi.saveConfig).toHaveBeenCalledWith(panel.config.value)
    expect(onSaved).toHaveBeenCalled()
  })

  it('warns before saving without base url', async () => {
    const panel = mountComposable(() => useLlmConfigPanel(vi.fn()))
    await settle()

    panel.config.value.base_url = ''
    await panel.handleTestAndSave()

    expect(messageMock.warning).toHaveBeenCalledWith('需要地址')
    expect(llmApi.testConnection).not.toHaveBeenCalled()
  })
})

describe('useAvatarDetailPanel helpers', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(avatarApi.setLongTermObjective).mockResolvedValue({})
    vi.mocked(avatarApi.clearLongTermObjective).mockResolvedValue({})
  })

  it('parses effect lines with source and fallback source', () => {
    expect(parseAvatarEffectLine('[功法] 攻击+1；速度+2', i18n.global.t)).toEqual({
      source: '功法',
      segments: ['攻击+1', '速度+2'],
    })
    expect(parseAvatarEffectLine('未标注效果', i18n.global.t)).toEqual({
      source: '其他',
      segments: ['未标注效果'],
    })
  })

  it('builds relation meta lines without stranger attitude', () => {
    expect(buildAvatarRelationMetaLines({
      target_id: 'a2',
      name: '青岚',
      relation: '道侣 / 友好',
      relation_type: 'lover',
      numeric_relation: 'friend',
      friendliness: 12,
      realm: 'QI_REFINEMENT',
      sect: '青云宗',
    })).toEqual(['道侣', '友好（12）'])

    expect(buildAvatarRelationMetaLines({
      target_id: 'a3',
      name: '陌生人',
      relation: '陌生',
      relation_type: '',
      numeric_relation: 'stranger',
      friendliness: 0,
      realm: 'QI_REFINEMENT',
      sect: '',
    })).toEqual([])
  })

  it('groups relations, formats rank, and updates objectives', async () => {
    const refreshDetail = vi.fn()
    const select = vi.fn()
    const panel = mountComposable(() => useAvatarDetailPanel(
      avatarData,
      i18n.global.t,
      { value: 'zh-CN' },
      { refreshDetail, select } as any,
      () => true,
      vi.fn(),
    ))

    expect(panel.formattedRanking.value).toBe('天榜第二')
    expect(panel.parsedCurrentEffects.value).toHaveLength(2)
    expect(panel.groupedRelations.value.parents).toHaveLength(2)

    panel.objectiveContent.value = '闭关突破'
    await panel.handleSetObjective()
    expect(avatarApi.setLongTermObjective).toHaveBeenCalledWith('a1', '闭关突破')
    expect(refreshDetail).toHaveBeenCalled()

    await panel.handleClearObjective()
    expect(avatarApi.clearLongTermObjective).toHaveBeenCalledWith('a1')
  })
})
