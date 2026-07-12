import { beforeEach, describe, expect, it, vi } from 'vitest'

const playMock = vi.hoisted(() => vi.fn())

vi.mock('@/composables/useAudio', () => ({
  useAudio: () => ({
    play: playMock,
  }),
}))

import { setupGlobalSound } from '@/utils/globalSound'

describe('setupGlobalSound', () => {
  beforeEach(() => {
    playMock.mockClear()
    document.body.innerHTML = ''
  })

  it('plays the default click sound for interactive elements', () => {
    const cleanup = setupGlobalSound()
    const button = document.createElement('button')
    document.body.appendChild(button)

    button.click()

    expect(playMock).toHaveBeenCalledWith('click')
    cleanup()
  })

  it('skips elements with dedicated or disabled sound markers', () => {
    const cleanup = setupGlobalSound()
    const customSoundButton = document.createElement('button')
    customSoundButton.setAttribute('data-has-sound', 'select')
    const mutedButton = document.createElement('button')
    mutedButton.setAttribute('data-no-sound', '')
    document.body.append(customSoundButton, mutedButton)

    customSoundButton.click()
    mutedButton.click()

    expect(playMock).not.toHaveBeenCalled()
    cleanup()
  })

  it('does not play after cleanup', () => {
    const cleanup = setupGlobalSound()
    const button = document.createElement('button')
    document.body.appendChild(button)

    cleanup()
    button.click()

    expect(playMock).not.toHaveBeenCalled()
  })
})
