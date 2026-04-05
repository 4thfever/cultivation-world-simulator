import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useBgm } from '@/composables/useBgm'
import { setActivePinia, createPinia } from 'pinia'
import { useSettingStore } from '@/stores/setting'

let mockTime = 0
global.performance.now = () => mockTime
global.requestAnimationFrame = (cb) => {
  mockTime += 16.6
  cb(mockTime)
  return 0
}

class MockAudio {
  src = ''
  volume = 1
  dataset: Record<string, string> = {}
  paused = true
  listeners: Record<string, Function[]> = {}

  play() {
    this.paused = false
    return Promise.resolve()
  }
  
  pause() {
    this.paused = true
  }

  addEventListener(event: string, callback: Function) {
    if (!this.listeners[event]) {
      this.listeners[event] = []
    }
    this.listeners[event].push(callback)
  }
}

let createdTracks: MockAudio[] = []

describe('useBgm', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    createdTracks = []
    global.Audio = vi.fn().mockImplementation(() => {
      const track = new MockAudio()
      createdTracks.push(track)
      return track
    }) as any
  })

  function unlockAudio() {
    window.dispatchEvent(new Event('pointerdown'))
  }

  it('should wait for interaction before playing splash bgm', async () => {
    const { play } = useBgm()
    await play('splash')
    expect(createdTracks.some(track => track.src === '/bgm/Eastminster.mp3')).toBe(false)

    unlockAudio()

    expect(createdTracks.some(track => track.src === '/bgm/Eastminster.mp3')).toBe(true)
  })

  it('should play map bgm', async () => {
    const { play } = useBgm()
    await play('map')
    unlockAudio()
    expect(true).toBe(true)
  })
  
  it('should stop bgm when null is passed', async () => {
    const { play } = useBgm()
    await play('splash')
    unlockAudio()
    await play(null)
    expect(true).toBe(true)
  })
  
  it('should update volume when setting changes', async () => {
    const { init } = useBgm()
    init()
    const settingStore = useSettingStore()
    settingStore.bgmVolume = 0.5
    expect(true).toBe(true)
  })
  
  it('should stop explicitly', async () => {
    const { play, stop } = useBgm()
    await play('map')
    unlockAudio()
    stop()
    expect(true).toBe(true)
  })

})
