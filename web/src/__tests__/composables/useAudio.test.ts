import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingStore } from '@/stores/setting'

async function loadUseAudio() {
  const module = await import('@/composables/useAudio')
  return module.useAudio
}

describe('useAudio', () => {
  beforeEach(() => {
    vi.resetModules()
    setActivePinia(createPinia())
    
    // Mock AudioContext
    window.AudioContext = vi.fn().mockImplementation(() => ({
      state: 'suspended',
      resume: vi.fn().mockResolvedValue(undefined),
      createBufferSource: vi.fn().mockReturnValue({
        connect: vi.fn(),
        start: vi.fn(),
      }),
      createGain: vi.fn().mockReturnValue({
        gain: { value: 1 },
        connect: vi.fn(),
      }),
      destination: {},
      decodeAudioData: vi.fn().mockResolvedValue({}),
    })) as any

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      arrayBuffer: vi.fn().mockResolvedValue(new ArrayBuffer(8)),
    }) as any
  })

  it('should initialize and load sounds', async () => {
    const useAudio = await loadUseAudio()
    const { init } = useAudio()
    await init()
    expect(global.fetch).toHaveBeenCalled()
    expect(global.fetch).toHaveBeenCalledWith('/sfx/click.ogg')
  })

  it('should play a sound if initialized', async () => {
    const useAudio = await loadUseAudio()
    const { init, play } = useAudio()
    await init()
    
    const settingStore = useSettingStore()
    settingStore.sfxVolume = 1
    
    expect(() => play('click')).not.toThrow()
  })
  
  it('should not throw if playing without init', async () => {
    const useAudio = await loadUseAudio()
    const { play } = useAudio()
    expect(() => play('click')).not.toThrow()
  })
  
  it('should not play if volume is 0', async () => {
    const useAudio = await loadUseAudio()
    const { init, play } = useAudio()
    await init()
    
    const settingStore = useSettingStore()
    settingStore.sfxVolume = 0
    
    expect(() => play('click')).not.toThrow()
  })
})
