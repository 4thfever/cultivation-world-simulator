import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach } from 'vitest'
import AnimatedAvatar from '@/components/game/AnimatedAvatar.vue'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

describe('AnimatedAvatar', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render successfully', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'zh-CN',
      messages: {}
    })

    const wrapper = mount(AnimatedAvatar, {
      props: {
        avatar: { x: 0, y: 0, state: 'idle' } as any,
        tileSize: 32,
        isHovered: false,
        isSelected: false
      },
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          container: true,
          animatedSprite: true,
          graphics: true,
          sprite: true,
        },
        config: {
          compilerOptions: {
            isCustomElement: (tag) => ['container', 'graphics', 'sprite', 'text'].includes(tag),
          },
        },
      }
    })

    expect(wrapper.exists()).toBe(true)
  })
})
