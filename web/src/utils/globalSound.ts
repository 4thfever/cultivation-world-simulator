import { useAudio } from '@/composables/useAudio'

const INTERACTIVE_SELECTOR = 'button, a, [role="button"], .n-button, .btn, .clickable'

export function setupGlobalSound(target: Window = window): () => void {
  const { play } = useAudio()

  const handleClick = (event: MouseEvent) => {
    const eventTarget = event.target
    if (!(eventTarget instanceof HTMLElement)) return

    const interactiveEl = eventTarget.closest<HTMLElement>(INTERACTIVE_SELECTOR)
    if (!interactiveEl) return
    if (interactiveEl.hasAttribute('data-no-sound')) return
    if (interactiveEl.hasAttribute('data-has-sound')) return
    if (
      interactiveEl instanceof HTMLButtonElement &&
      (interactiveEl.disabled || interactiveEl.classList.contains('n-button--disabled'))
    ) {
      return
    }

    play('click')
  }

  // Capture-phase listening keeps UI feedback consistent even when inner controls stop propagation.
  target.addEventListener('click', handleClick, { capture: true })
  return () => target.removeEventListener('click', handleClick, { capture: true })
}
