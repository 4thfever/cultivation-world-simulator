import { defineComponent, nextTick, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useMapStore } from '@/stores/map'

const mockTexture = vi.hoisted(() => ({ valid: true }))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    locale: ref('zh-CN'),
  }),
}))

vi.mock('@/composables/useAudio', () => ({
  useAudio: () => ({
    play: vi.fn(),
  }),
}))

vi.mock('@/components/game/composables/useTextures', () => ({
  useTextures: () => ({
    textures: ref({
      PLAIN: mockTexture,
      SEA: mockTexture,
      WATER: mockTexture,
    }),
    isLoaded: ref(true),
    preloadRegionTextures: vi.fn().mockResolvedValue(undefined),
    getTileTexture: vi.fn(() => mockTexture),
  }),
}))

const spriteDestroyMock = vi.hoisted(() => vi.fn())
const graphicsDestroyMock = vi.hoisted(() => vi.fn())
const tilingSpriteDestroyMock = vi.hoisted(() => vi.fn())
const tickerDestroyMock = vi.hoisted(() => vi.fn())
const tickerStopMock = vi.hoisted(() => vi.fn())
const containerDestroyMock = vi.hoisted(() => vi.fn())

vi.mock('pixi.js', () => ({
  Container: class {
    children: Array<{ destroy?: (options?: unknown) => void }> = []
    addChild(child: { destroy?: (options?: unknown) => void }) {
      this.children.push(child)
      return child
    }
    removeChildren() {
      return this.children.splice(0, this.children.length)
    }
    destroy(options?: { children?: boolean }) {
      containerDestroyMock(options)
      if (options?.children) {
        this.children.forEach(child => child.destroy?.(options))
      }
    }
  },
  Sprite: class {
    x = 0
    y = 0
    width = 0
    height = 0
    roundPixels = false
    eventMode = 'none'
    constructor(public texture: unknown) {}
    destroy = spriteDestroyMock
  },
  Graphics: class {
    rect() {
      return this
    }
    fill() {
      return this
    }
    destroy = graphicsDestroyMock
  },
  TilingSprite: class {
    tileScale = { set: vi.fn() }
    tilePosition = { x: 0, y: 0 }
    mask: unknown = null
    constructor(public options: unknown) {}
    destroy = tilingSpriteDestroyMock
  },
  Ticker: class {
    add = vi.fn()
    start = vi.fn()
    stop = tickerStopMock
    destroy = tickerDestroyMock
  },
}))

import { useMapLayerRenderer } from '@/components/game/composables/useMapLayerRenderer'

function createMockContainer() {
  const children: Array<{ destroy: ReturnType<typeof vi.fn> }> = []
  return {
    children,
    addChild(child: { destroy: ReturnType<typeof vi.fn> }) {
      children.push(child)
      return child
    },
    removeChildren() {
      return children.splice(0, children.length)
    },
  }
}

describe('useMapLayerRenderer', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('destroys old Pixi display objects before rerendering the map', async () => {
    const mapStore = useMapStore()
    mapStore.mapData = [['PLAIN']]

    const container = createMockContainer()
    mount(defineComponent({
      setup() {
        const renderer = useMapLayerRenderer(vi.fn())
        renderer.mapContainer.value = container as never
        return () => null
      },
    }))

    mapStore.isLoaded = true
    await nextTick()
    await nextTick()
    const firstRenderChildren = [...container.children]
    expect(firstRenderChildren.length).toBeGreaterThan(0)

    mapStore.mapData = [['PLAIN', 'PLAIN']]
    mapStore.isLoaded = false
    await nextTick()
    mapStore.isLoaded = true
    await nextTick()
    await nextTick()

    expect(containerDestroyMock).toHaveBeenCalledWith({ children: true, texture: false })
    expect(spriteDestroyMock).toHaveBeenCalledWith({ children: true, texture: false })
  })
})
