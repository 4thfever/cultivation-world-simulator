import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { systemApi, type InitStatusDTO } from '@/api'
import { logError } from '@/utils/appError'

const PROGRESS_RING_RADIUS = 90
const PROGRESS_RING_CIRCUMFERENCE = 2 * Math.PI * PROGRESS_RING_RADIUS

export function useLoadingOverlayState(status: () => InitStatusDTO | null) {
  const { t, tm } = useI18n()

  const tipsList = computed<string[]>(() => {
    const list = tm('loading.tips') as unknown
    return Array.isArray(list) ? list.filter((item): item is string => typeof item === 'string') : []
  })

  const currentTip = ref('')
  const displayProgress = ref(0)
  const localElapsed = ref(0)
  let tipInterval: ReturnType<typeof setInterval> | null = null
  let elapsedInterval: ReturnType<typeof setInterval> | null = null

  const progress = computed(() => displayProgress.value)
  const phaseText = computed(() => {
    const phaseName = status()?.phase_name || ''
    if (!phaseName) return t('loading.phase.chaos')
    return t(`loading.phase.${phaseName}`)
  })
  const isError = computed(() => status()?.status === 'error')
  const errorMessage = computed(() => status()?.error || t('loading.unknown_error'))
  const bgOpacity = computed(() => {
    const elapsed = localElapsed.value
    if (elapsed <= 5) return 1
    if (elapsed >= 20) return 0.9
    return 1 - (elapsed - 5) / 15 * 0.1
  })
  const strokeDashoffset = computed(() => (
    PROGRESS_RING_CIRCUMFERENCE - (progress.value / 100) * PROGRESS_RING_CIRCUMFERENCE
  ))

  watch(tipsList, (list) => {
    if (list.length > 0 && !currentTip.value) {
      currentTip.value = list[Math.floor(Math.random() * list.length)]
    }
  }, { immediate: true })

  watch(() => status()?.progress, (newVal) => {
    if (newVal !== undefined && newVal !== null && newVal > displayProgress.value) {
      displayProgress.value = newVal
    }
  }, { immediate: true })

  watch(() => status()?.status, (newStatus, oldStatus) => {
    if (oldStatus === 'ready' && newStatus !== 'ready') {
      localElapsed.value = 0
      displayProgress.value = 0
    }
  })

  async function handleRetry() {
    localElapsed.value = 0
    displayProgress.value = 0
    try {
      await systemApi.reinitGame()
    } catch (e: unknown) {
      logError('LoadingOverlay reinit game', e)
    }
  }

  function startTimers() {
    tipInterval = setInterval(() => {
      if (tipsList.value.length > 0) {
        const idx = Math.floor(Math.random() * tipsList.value.length)
        currentTip.value = tipsList.value[idx]
      }
    }, 5000)

    elapsedInterval = setInterval(() => {
      localElapsed.value++

      const currentStatus = status()
      if (currentStatus?.status !== 'in_progress' || displayProgress.value >= 99) return

      const currentPhase = currentStatus.phase ?? 0
      const progressMap: Record<number, number> = { 0: 0, 1: 10, 2: 25, 3: 40, 4: 55, 5: 70, 6: 85 }
      const nextPhaseStart = progressMap[currentPhase + 1] ?? 100

      if (displayProgress.value < nextPhaseStart - 1 || currentPhase === 6) {
        displayProgress.value++
      }
    }, 1000)
  }

  function stopTimers() {
    if (tipInterval) {
      clearInterval(tipInterval)
      tipInterval = null
    }
    if (elapsedInterval) {
      clearInterval(elapsedInterval)
      elapsedInterval = null
    }
  }

  onMounted(startTimers)
  onUnmounted(stopTimers)

  return {
    currentTip,
    progress,
    phaseText,
    isError,
    errorMessage,
    bgOpacity,
    localElapsed,
    radius: PROGRESS_RING_RADIUS,
    circumference: PROGRESS_RING_CIRCUMFERENCE,
    strokeDashoffset,
    handleRetry,
  }
}
