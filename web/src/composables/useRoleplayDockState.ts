import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

import { eventApi } from '@/api'
import { mapEventDtosToTimeline } from '@/api/mappers/event'
import { useRoleplayStore } from '@/stores/roleplay'
import type { GameEvent } from '@/types/core'
import { logError } from '@/utils/appError'

export function useRoleplayDockState() {
  const roleplayStore = useRoleplayStore()
  const commandText = ref('')
  const localEvents = ref<GameEvent[]>([])
  const eventListRef = ref<HTMLElement | null>(null)

  let pollTimer: ReturnType<typeof setInterval> | null = null

  const session = computed(() => roleplayStore.session)
  const pending = computed(() => session.value.pending_request)
  const conversationSession = computed(() => session.value.conversation_session)
  const interactionHistory = computed(() => session.value.interaction_history ?? [])
  const controlledAvatarId = computed(() => session.value.controlled_avatar_id ?? '')
  const hasActiveRoleplay = computed(() => !!controlledAvatarId.value)
  const isDecision = computed(() => pending.value?.type === 'decision')
  const isChoice = computed(() => pending.value?.type === 'choice')
  const isConversation = computed(() => pending.value?.type === 'conversation')
  const requestKind = computed<'decision' | 'choice' | 'conversation' | 'none'>(() => {
    if (isDecision.value) return 'decision'
    if (isChoice.value) return 'choice'
    if (isConversation.value) return 'conversation'
    return 'none'
  })
  const displayEvents = computed(() => localEvents.value)
  const avatarName = computed(() => {
    const context = session.value.last_prompt_context ?? {}
    const rawName = typeof context.avatar_name === 'string' ? context.avatar_name : ''
    return rawName || controlledAvatarId.value || '角色'
  })
  const conversationTargetName = computed(() => {
    const context = session.value.last_prompt_context ?? {}
    const rawName = typeof context.target_avatar_name === 'string' ? context.target_avatar_name : ''
    return rawName || '对方'
  })
  const conversationMessages = computed(
    () => pending.value?.messages ?? conversationSession.value?.messages ?? []
  )
  const statusText = computed(() => {
    if (session.value.status === 'awaiting_decision') return '等待指令'
    if (session.value.status === 'awaiting_choice') return '等待选择'
    if (session.value.status === 'conversing') return '对话中'
    if (session.value.status === 'submitting') return '提交中'
    if (hasActiveRoleplay.value) return '观察中'
    return ''
  })
  const requestSummary = computed(() => {
    if (isDecision.value) return '需要决定下一步行动'
    if (isChoice.value) return pending.value?.description || '需要做出回应'
    if (isConversation.value) return `正在与 ${conversationTargetName.value} 交谈`
    return '当前动作链仍在执行'
  })
  const requestPanelTitle = computed(() => {
    if (isDecision.value) return '决策'
    if (isChoice.value) return '选项'
    if (isConversation.value) return '对话'
    return '观察'
  })
  const requestPanelCaption = computed(() => {
    if (isDecision.value) return '输入一句意图，系统会扩展成行动链'
    if (isChoice.value) return '从有限选项里做出一次回应'
    if (isConversation.value) return `玩家控制 ${avatarName.value} 发言，对方由 LLM 回复`
    return '当前没有需要立即处理的请求'
  })
  const requestErrorText = computed(() => roleplayStore.error || '')
  const decisionSubmitText = computed(() => roleplayStore.isSubmitting ? '处理中...' : '提交指令')
  const choiceSubmittingText = computed(() => roleplayStore.isSubmitting ? '正在处理选择，请稍候...' : '')
  const conversationSubmitText = computed(() => roleplayStore.isSubmitting ? '发送中...' : '发送')
  const mainLayoutClass = computed(() => ({
    'roleplay-dock__main--conversation': requestKind.value === 'conversation',
  }))

  async function refreshRoleplayState() {
    await roleplayStore.fetchSession()
  }

  async function refreshLocalEvents() {
    if (!controlledAvatarId.value) {
      localEvents.value = []
      return
    }
    try {
      const page = await eventApi.fetchEvents({ avatar_id: controlledAvatarId.value, limit: 18 })
      localEvents.value = mapEventDtosToTimeline(page.events)
    } catch (e) {
      logError('RoleplayDock refresh events', e)
    }
  }

  async function handleSubmitDecision() {
    if (!pending.value?.request_id || !controlledAvatarId.value || !commandText.value.trim()) return
    await roleplayStore.submitDecision({
      avatar_id: controlledAvatarId.value,
      request_id: pending.value.request_id,
      command_text: commandText.value.trim(),
    })
    commandText.value = ''
  }

  async function handleSubmitChoice(selectedKey: string) {
    if (!pending.value?.request_id || !controlledAvatarId.value) return
    await roleplayStore.submitChoice({
      avatar_id: controlledAvatarId.value,
      request_id: pending.value.request_id,
      selected_key: selectedKey,
    })
  }

  async function handleStopRoleplay() {
    if (!controlledAvatarId.value) return
    await roleplayStore.stopRoleplay(controlledAvatarId.value)
  }

  async function handleSendConversation() {
    if (!pending.value?.request_id || !controlledAvatarId.value || !commandText.value.trim()) return
    await roleplayStore.sendConversation({
      avatar_id: controlledAvatarId.value,
      request_id: pending.value.request_id,
      message: commandText.value.trim(),
    })
    commandText.value = ''
  }

  async function handleEndConversation() {
    if (!pending.value?.request_id || !controlledAvatarId.value) return
    await roleplayStore.endConversation({
      avatar_id: controlledAvatarId.value,
      request_id: pending.value.request_id,
    })
  }

  function formatEventDate(event: GameEvent) {
    return `${event.year}年${event.month}月`
  }

  function startPolling() {
    if (pollTimer) return
    pollTimer = setInterval(() => {
      void refreshRoleplayState()
      void refreshLocalEvents()
    }, 1000)
  }

  function stopPolling() {
    if (!pollTimer) return
    clearInterval(pollTimer)
    pollTimer = null
  }

  watch(controlledAvatarId, () => {
    void refreshLocalEvents()
  })

  watch(
    displayEvents,
    () => {
      const el = eventListRef.value
      if (!el) return

      const isScrollable = el.scrollHeight > el.clientHeight
      const isAtBottom = !isScrollable || (el.scrollHeight - el.scrollTop - el.clientHeight < 50)

      if (isAtBottom) {
        nextTick(() => {
          if (eventListRef.value) {
            eventListRef.value.scrollTop = eventListRef.value.scrollHeight
          }
        })
      }
    },
    { deep: true }
  )

  onMounted(() => {
    void refreshRoleplayState()
    void refreshLocalEvents()
    startPolling()
  })

  onUnmounted(() => {
    stopPolling()
  })

  return {
    roleplayStore,
    commandText,
    eventListRef,
    pending,
    hasActiveRoleplay,
    isDecision,
    isChoice,
    isConversation,
    displayEvents,
    avatarName,
    conversationTargetName,
    conversationMessages,
    interactionHistory,
    statusText,
    requestSummary,
    requestPanelTitle,
    requestPanelCaption,
    requestErrorText,
    decisionSubmitText,
    choiceSubmittingText,
    conversationSubmitText,
    mainLayoutClass,
    handleSubmitDecision,
    handleSubmitChoice,
    handleStopRoleplay,
    handleSendConversation,
    handleEndConversation,
    formatEventDate,
  }
}
