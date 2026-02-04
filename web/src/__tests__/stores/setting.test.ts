import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Use vi.hoisted to define mock functions that will be used by vi.mock.
const { mockSetLanguage } = vi.hoisted(() => ({
  mockSetLanguage: vi.fn().mockResolvedValue(undefined),
}))

// Create a fresh mock i18n object for each test.
let mockI18nLocale: { value: string } | string = { value: 'zh-CN' }
let mockI18nMode = 'composition'

// Mock i18n.
vi.mock('@/locales', () => ({
  default: {
    get mode() { return mockI18nMode },
    global: {
      get locale() { return mockI18nLocale },
      set locale(val) { mockI18nLocale = val },
    },
  },
}))

// Mock systemApi.
vi.mock('@/api/modules/system', () => ({
  systemApi: {
    setLanguage: mockSetLanguage,
  },
}))

import { useSettingStore } from '@/stores/setting'

describe('useSettingStore', () => {
  let store: ReturnType<typeof useSettingStore>
  let localStorageMock: Record<string, string>

  beforeEach(() => {
    // Reset localStorage mock.
    localStorageMock = {}
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key: string) => {
      return localStorageMock[key] || null
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation((key: string, value: string) => {
      localStorageMock[key] = value
    })

    // Reset mocks.
    vi.clearAllMocks()
    mockI18nLocale = { value: 'zh-CN' }
    mockI18nMode = 'composition'

    setActivePinia(createPinia())
    store = useSettingStore()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('should read locale from localStorage if available', () => {
      // Reset with new localStorage value.
      localStorageMock = { app_locale: 'en-US' }
      setActivePinia(createPinia())
      const newStore = useSettingStore()

      expect(newStore.locale).toBe('en-US')
    })

    it('should default to zh-CN if localStorage is empty', () => {
      expect(store.locale).toBe('zh-CN')
    })
  })

  describe('setLocale', () => {
    it('should update locale value', async () => {
      await store.setLocale('en-US')

      expect(store.locale).toBe('en-US')
    })

    it('should save locale to localStorage', async () => {
      await store.setLocale('zh-TW')

      expect(localStorageMock.app_locale).toBe('zh-TW')
    })

    it('should update i18n.global.locale in composition mode', async () => {
      mockI18nMode = 'composition'
      mockI18nLocale = { value: 'zh-CN' }

      await store.setLocale('en-US')

      expect((mockI18nLocale as { value: string }).value).toBe('en-US')
    })

    it('should update i18n.global.locale in legacy mode', async () => {
      mockI18nMode = 'legacy'
      mockI18nLocale = 'zh-CN'

      await store.setLocale('en-US')

      expect(mockI18nLocale).toBe('en-US')
    })

    it('should update document.documentElement.lang', async () => {
      await store.setLocale('en-US')

      expect(document.documentElement.lang).toBe('en')
    })

    it('should set correct HTML lang for zh-CN', async () => {
      await store.setLocale('zh-CN')

      expect(document.documentElement.lang).toBe('zh-CN')
    })

    it('should set correct HTML lang for zh-TW', async () => {
      await store.setLocale('zh-TW')

      expect(document.documentElement.lang).toBe('zh-TW')
    })

    it('should call syncBackend after updating locale', async () => {
      await store.setLocale('en-US')

      expect(mockSetLanguage).toHaveBeenCalledWith('en-US')
    })
  })

  describe('syncBackend', () => {
    it('should call systemApi.setLanguage with current locale', async () => {
      store.locale = 'zh-TW'

      await store.syncBackend()

      expect(mockSetLanguage).toHaveBeenCalledWith('zh-TW')
    })

    it('should catch errors and log warning', async () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      mockSetLanguage.mockRejectedValueOnce(new Error('Network error'))

      await store.syncBackend()

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to sync language with backend:',
        expect.any(Error)
      )

      consoleSpy.mockRestore()
    })

    it('should not throw when API fails', async () => {
      mockSetLanguage.mockRejectedValueOnce(new Error('API error'))

      // Should not throw.
      await expect(store.syncBackend()).resolves.not.toThrow()
    })
  })
})
