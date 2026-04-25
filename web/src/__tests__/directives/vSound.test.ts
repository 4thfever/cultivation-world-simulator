import { mount } from '@vue/test-utils'
import { defineComponent, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const playMock = vi.hoisted(() => vi.fn())

vi.mock('@/composables/useAudio', () => ({
  useAudio: () => ({
    play: playMock,
  }),
}))

import { vSound } from '@/directives/vSound'

const SoundButton = defineComponent({
  setup() {
    const sound = ref('select')
    return { sound }
  },
  template: '<button v-sound="sound">play</button>',
})

describe('vSound', () => {
  beforeEach(() => {
    playMock.mockClear()
  })

  it('uses the latest sound type after updates', async () => {
    const wrapper = mount(SoundButton, {
      global: {
        directives: {
          sound: vSound,
        },
      },
    })

    await wrapper.find('button').trigger('click')
    expect(playMock).toHaveBeenLastCalledWith('select')

    wrapper.vm.sound = 'cancel'
    await wrapper.vm.$nextTick()
    await wrapper.find('button').trigger('click')

    expect(playMock).toHaveBeenLastCalledWith('cancel')
  })

  it('removes the click listener on unmount', async () => {
    const wrapper = mount(SoundButton, {
      attachTo: document.body,
      global: {
        directives: {
          sound: vSound,
        },
      },
    })
    const button = wrapper.find('button').element

    wrapper.unmount()
    button.click()

    expect(playMock).not.toHaveBeenCalled()
  })
})
