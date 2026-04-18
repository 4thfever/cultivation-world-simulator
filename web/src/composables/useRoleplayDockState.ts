import { computed, onMounted, onUnmounted, ref } from 'vue'

import { useRoleplayStore } from '@/stores/roleplay'

export function useRoleplayDockState() {
  const roleplayStore = useRoleplayStore()
  const commandText = ref('')
  const optimisticConversationMessage = ref<{
    id: string
    role: string
    speaker_name: string
    content: string
    created_at: number
  } | null>(null)
  const isConversationAwaitingReply = ref(false)

  let pollTimer: ReturnType<typeof setInterval> | null = null

  const session = computed(() => roleplayStore.session)
  const pending = computed(() => session.value.pending_request)
  const conversationSession = computed(() => session.value.conversation_session)
  const interactionHistory = computed(() => {
    const baseItems = [...(session.value.interaction_history ?? [])]
    const optimisticMessage = optimisticConversationMessage.value
    if (optimisticMessage) {
      baseItems.push({
        type: 'conversation_player',
        created_at: optimisticMessage.created_at,
        text: optimisticMessage.content,
      })
    }
    return baseItems
  })
  const controlledAvatarId = computed(() => session.value.controlled_avatar_id ?? '')
  const hasActiveRoleplay = computed(() => !!controlledAvatarId.value)
  const isDecision = computed(() => pending.value?.type === 'decision')
  const isChoice = computed(() => pending.value?.type === 'choice')
  const isConversation = computed(() => pending.value?.type === 'conversation')
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
  const conversationMessages = computed(() => {
    const baseMessages = [...(pending.value?.messages ?? conversationSession.value?.messages ?? [])]
    const optimisticMessage = optimisticConversationMessage.value
    if (optimisticMessage) {
      baseMessages.push(optimisticMessage)
    }
    return baseMessages
  })
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
  const conversationSubmitText = computed(() => {
    if (isConversationAwaitingReply.value) return '等待回复...'
    if (roleplayStore.isSubmitting) return '发送中...'
    return '发送'
  })

  async function refreshRoleplayState() {
    await roleplayStore.fetchSession()
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
    const message = commandText.value.trim()
    const createdAt = Date.now()
    optimisticConversationMessage.value = {
      id: `optimistic-${createdAt}`,
      role: 'player',
      speaker_name: avatarName.value,
      content: message,
      created_at: createdAt,
    }
    commandText.value = ''
    isConversationAwaitingReply.value = true
    try {
      await roleplayStore.sendConversation({
        avatar_id: controlledAvatarId.value,
        request_id: pending.value.request_id,
        message,
      })
      optimisticConversationMessage.value = null
    } catch (e) {
      optimisticConversationMessage.value = null
      commandText.value = message
      throw e
    } finally {
      isConversationAwaitingReply.value = false
    }
  }

  async function handleEndConversation() {
    if (!pending.value?.request_id || !controlledAvatarId.value) return
    await roleplayStore.endConversation({
      avatar_id: controlledAvatarId.value,
      request_id: pending.value.request_id,
    })
  }

  function startPolling() {
    if (pollTimer) return
    pollTimer = setInterval(() => {
      void refreshRoleplayState()
    }, 1000)
  }

  function stopPolling() {
    if (!pollTimer) return
    clearInterval(pollTimer)
    pollTimer = null
  }

  onMounted(() => {
    void refreshRoleplayState()
    startPolling()
  })

  onUnmounted(() => {
    stopPolling()
  })

  return {
    roleplayStore,
    commandText,
    pending,
    hasActiveRoleplay,
    isDecision,
    isChoice,
    isConversation,
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
    isConversationAwaitingReply,
    handleSubmitDecision,
    handleSubmitChoice,
    handleStopRoleplay,
    handleSendConversation,
    handleEndConversation,
  }
}
