import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import SaveLoadPanel from '@/components/game/panels/system/SaveLoadPanel.vue'
import type { SaveFileDTO } from '@/types/api'

// Use real timers for this test file since we need async operations.
beforeEach(() => {
  vi.useRealTimers()
})

afterEach(() => {
  vi.useFakeTimers()
})

// Mock naive-ui components.
vi.mock('naive-ui', () => ({
  NModal: {
    name: 'NModal',
    template: '<div class="n-modal" v-if="show"><slot /><slot name="footer" /></div>',
    props: ['show', 'title', 'preset', 'maskClosable', 'closable'],
  },
  NInput: {
    name: 'NInput',
    template: '<input class="n-input" :value="value" @input="$emit(\'update:value\', $event.target.value)" :placeholder="placeholder" :disabled="disabled" />',
    props: ['value', 'placeholder', 'status', 'disabled'],
    emits: ['update:value'],
  },
  NButton: {
    name: 'NButton',
    template: '<button class="n-button" :disabled="disabled || loading" @click="$emit(\'click\')"><slot /></button>',
    props: ['type', 'loading', 'disabled'],
    emits: ['click'],
  },
  NSpin: {
    name: 'NSpin',
    template: '<div class="n-spin"></div>',
    props: ['size'],
  },
  NTooltip: {
    name: 'NTooltip',
    template: '<div class="n-tooltip"><slot name="trigger" /><slot /></div>',
    props: ['trigger'],
  },
  useMessage: () => ({
    success: vi.fn(),
    error: vi.fn(),
  }),
}))

// Mock stores.
vi.mock('@/stores/world', () => ({
  useWorldStore: () => ({
    reset: vi.fn(),
    initialize: vi.fn().mockResolvedValue(undefined),
  }),
}))

vi.mock('@/stores/ui', () => ({
  useUiStore: () => ({
    clearSelection: vi.fn(),
  }),
}))

// Mock API.
vi.mock('@/api', () => ({
  systemApi: {
    fetchSaves: vi.fn(),
    saveGame: vi.fn(),
    loadGame: vi.fn(),
  },
}))

import { systemApi } from '@/api'

// Create i18n instance for tests.
const i18n = createI18n({
  legacy: false,
  locale: 'en-US',
  messages: {
    'en-US': {
      save_load: {
        loading: 'Loading...',
        new_save: 'New Save',
        new_save_desc: 'Save with custom name',
        quick_save: 'Quick Save',
        quick_save_desc: 'Use auto-generated name',
        empty: 'No saves found',
        game_time: 'Game Time: {time}',
        avatar_count: 'Characters: {alive}/{total}',
        event_count: '{count} events',
        load: 'Load',
        save_success: 'Saved: {filename}',
        save_failed: 'Save failed',
        load_confirm: 'Load {filename}?',
        load_success: 'Loaded',
        load_failed: 'Load failed',
        fetch_failed: 'Fetch failed',
        save_modal_title: 'Save Game',
        save_confirm: 'Save',
        name_hint: 'Enter save name (optional)',
        name_placeholder: 'Enter name...',
        name_tip: 'Leave empty for auto name',
        name_too_long: 'Name too long',
        name_invalid_chars: 'Invalid characters',
      },
      common: {
        cancel: 'Cancel',
      },
    },
  },
})

const createMockSave = (overrides: Partial<SaveFileDTO> = {}): SaveFileDTO => ({
  filename: 'test_save.json',
  save_time: '2026-01-01T12:00:00',
  game_time: '100年1月',
  version: '1.0.0',
  language: 'zh-CN',
  avatar_count: 10,
  alive_count: 8,
  dead_count: 2,
  custom_name: null,
  event_count: 50,
  ...overrides,
})

// Helper to wait for promises.
const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0))

describe('SaveLoadPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })

  describe('Save Mode', () => {
    it('should render save actions in save mode', async () => {
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: [] })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'save' },
        global: { plugins: [i18n] },
      })

      await flushPromises()

      expect(wrapper.find('.new-save-card').exists()).toBe(true)
      expect(wrapper.find('.quick-save-card').exists()).toBe(true)
      expect(wrapper.text()).toContain('New Save')
      expect(wrapper.text()).toContain('Quick Save')
    })

    it('should open save modal when clicking new save', async () => {
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: [] })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'save' },
        global: { plugins: [i18n] },
      })

      await flushPromises()
      await wrapper.find('.new-save-card').trigger('click')
      await flushPromises()

      expect(wrapper.find('.n-modal').exists()).toBe(true)
    })

    it('should call saveGame without name on quick save', async () => {
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: [] })
      vi.mocked(systemApi.saveGame).mockResolvedValue({ status: 'ok', filename: 'auto_save.json' })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'save' },
        global: { plugins: [i18n] },
      })

      await flushPromises()
      await wrapper.find('.quick-save-card').trigger('click')
      await flushPromises()

      expect(systemApi.saveGame).toHaveBeenCalled()
      expect(systemApi.saveGame).toHaveBeenCalledWith()
    })
  })

  describe('Load Mode', () => {
    it('should render save list in load mode', async () => {
      const mockSaves = [
        createMockSave({ filename: 'save1.json', custom_name: '我的存档' }),
        createMockSave({ filename: 'save2.json', game_time: '200年6月' }),
      ]
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: mockSaves })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'load' },
        global: { plugins: [i18n] },
      })

      await flushPromises()

      expect(wrapper.findAll('.save-item')).toHaveLength(2)
      expect(wrapper.text()).toContain('我的存档')
      expect(wrapper.text()).toContain('Load')
    })

    it('should not render save actions in load mode', async () => {
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: [] })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'load' },
        global: { plugins: [i18n] },
      })

      await flushPromises()

      expect(wrapper.find('.new-save-card').exists()).toBe(false)
      expect(wrapper.find('.quick-save-card').exists()).toBe(false)
    })

    it('should call loadGame when clicking save item', async () => {
      const mockSaves = [createMockSave({ filename: 'test.json' })]
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: mockSaves })
      vi.mocked(systemApi.loadGame).mockResolvedValue({ status: 'ok', message: 'loaded' })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'load' },
        global: { plugins: [i18n] },
      })

      await flushPromises()
      await wrapper.find('.save-item').trigger('click')
      await flushPromises()

      expect(systemApi.loadGame).toHaveBeenCalledWith('test.json')
    })

    it('should not load if user cancels confirm', async () => {
      vi.spyOn(window, 'confirm').mockReturnValue(false)
      const mockSaves = [createMockSave({ filename: 'test.json' })]
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: mockSaves })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'load' },
        global: { plugins: [i18n] },
      })

      await flushPromises()
      await wrapper.find('.save-item').trigger('click')
      await flushPromises()

      expect(systemApi.loadGame).not.toHaveBeenCalled()
    })
  })

  describe('Save Display', () => {
    it('should display custom name when available', async () => {
      const mockSaves = [createMockSave({ custom_name: '自定义名称', filename: 'test.json' })]
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: mockSaves })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'load' },
        global: { plugins: [i18n] },
      })

      await flushPromises()

      expect(wrapper.find('.save-name').text()).toBe('自定义名称')
    })

    it('should display filename when no custom name', async () => {
      const mockSaves = [createMockSave({ custom_name: null, filename: '20260101_120000.json' })]
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: mockSaves })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'load' },
        global: { plugins: [i18n] },
      })

      await flushPromises()

      expect(wrapper.find('.save-name').text()).toBe('20260101_120000')
    })


    it('should display avatar counts', async () => {
      const mockSaves = [createMockSave({ alive_count: 15, avatar_count: 20 })]
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: mockSaves })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'load' },
        global: { plugins: [i18n] },
      })

      await flushPromises()

      expect(wrapper.find('.avatar-count').text()).toContain('15')
      expect(wrapper.find('.avatar-count').text()).toContain('20')
    })

    it('should display event count', async () => {
      const mockSaves = [createMockSave({ event_count: 100 })]
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: mockSaves })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'load' },
        global: { plugins: [i18n] },
      })

      await flushPromises()

      expect(wrapper.find('.event-count').text()).toContain('100')
    })
  })

  describe('Name Validation', () => {
    it('should show error for name over 50 chars', async () => {
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: [] })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'save' },
        global: { plugins: [i18n] },
      })

      await flushPromises()
      await wrapper.find('.new-save-card').trigger('click')
      await flushPromises()

      const input = wrapper.find('.n-input')
      await input.setValue('a'.repeat(51))
      await flushPromises()

      expect(wrapper.find('.error-text').exists()).toBe(true)
      expect(wrapper.text()).toContain('Name too long')
    })

    it('should show error for invalid characters', async () => {
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: [] })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'save' },
        global: { plugins: [i18n] },
      })

      await flushPromises()
      await wrapper.find('.new-save-card').trigger('click')
      await flushPromises()

      const input = wrapper.find('.n-input')
      await input.setValue('name!@#$')
      await flushPromises()

      expect(wrapper.find('.error-text').exists()).toBe(true)
      expect(wrapper.text()).toContain('Invalid characters')
    })

    it('should allow valid Chinese name', async () => {
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: [] })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'save' },
        global: { plugins: [i18n] },
      })

      await flushPromises()
      await wrapper.find('.new-save-card').trigger('click')
      await flushPromises()

      const input = wrapper.find('.n-input')
      await input.setValue('我的存档')
      await flushPromises()

      expect(wrapper.find('.error-text').exists()).toBe(false)
    })

    it('should allow empty name', async () => {
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: [] })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'save' },
        global: { plugins: [i18n] },
      })

      await flushPromises()
      await wrapper.find('.new-save-card').trigger('click')
      await flushPromises()

      const input = wrapper.find('.n-input')
      await input.setValue('')
      await flushPromises()

      expect(wrapper.find('.error-text').exists()).toBe(false)
      expect(wrapper.find('.tip-text').exists()).toBe(true)
    })
  })

  describe('Empty State', () => {
    it('should show empty message when no saves', async () => {
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: [] })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'load' },
        global: { plugins: [i18n] },
      })

      await flushPromises()

      expect(wrapper.find('.empty').exists()).toBe(true)
      expect(wrapper.text()).toContain('No saves found')
    })
  })

  describe('Error Handling', () => {
    it('should handle fetchSaves error gracefully', async () => {
      vi.mocked(systemApi.fetchSaves).mockRejectedValue(new Error('Network error'))

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'load' },
        global: { plugins: [i18n] },
      })

      await flushPromises()

      // Should not crash, saves should be empty.
      expect(wrapper.findAll('.save-item')).toHaveLength(0)
    })

    it('should handle saveGame error gracefully', async () => {
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: [] })
      vi.mocked(systemApi.saveGame).mockRejectedValue(new Error('Save error'))

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'save' },
        global: { plugins: [i18n] },
      })

      await flushPromises()
      await wrapper.find('.quick-save-card').trigger('click')
      await flushPromises()

      // Should not crash.
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('Mode Switching', () => {
    it('should refetch saves when mode changes', async () => {
      vi.mocked(systemApi.fetchSaves).mockResolvedValue({ saves: [] })

      const wrapper = mount(SaveLoadPanel, {
        props: { mode: 'save' },
        global: { plugins: [i18n] },
      })

      await flushPromises()
      expect(systemApi.fetchSaves).toHaveBeenCalledTimes(1)

      await wrapper.setProps({ mode: 'load' })
      await flushPromises()

      expect(systemApi.fetchSaves).toHaveBeenCalledTimes(2)
    })
  })
})
