import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { useRoleplayStore } from '@/stores/roleplay'
import type { RoleplayInteractionRecordDTO } from '@/types/api'

export function useRoleplayDockState() {
  const { t } = useI18n()
  const roleplayStore = useRoleplayStore()
  const commandText = ref('')
  const optimisticConversationMessage = ref<{
    id: string
    role: 'player'
    speaker_name: string
    content: string
    created_at: number
  } | null>(null)
  const optimisticInteractionRecord = ref<RoleplayInteractionRecordDTO | null>(null)
  const isConversationAwaitingReply = ref(false)

  let pollTimer: ReturnType<typeof setInterval> | null = null

  const session = computed(() => roleplayStore.session)
  const pending = computed(() => session.value.pending_request)
  const conversationSession = computed(() => session.value.conversation_session)
  const interactionHistory = computed(() => {
    const baseItems = [...(session.value.interaction_history ?? [])]
    const optimisticRecord = optimisticInteractionRecord.value
    if (optimisticRecord) {
      baseItems.push(optimisticRecord)
    }
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
    return rawName || controlledAvatarId.value || t('game.roleplay.fallback.avatar_name')
  })
  const conversationTargetName = computed(() => {
    const context = session.value.last_prompt_context ?? {}
    const rawName = typeof context.target_avatar_name === 'string' ? context.target_avatar_name : ''
    return rawName || t('game.roleplay.fallback.counterpart_name')
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
    if (session.value.status === 'awaiting_decision') return t('game.roleplay.status.awaiting_decision')
    if (session.value.status === 'awaiting_choice') return t('game.roleplay.status.awaiting_choice')
    if (session.value.status === 'conversing') return t('game.roleplay.status.conversing')
    if (session.value.status === 'submitting') return t('game.roleplay.status.submitting')
    if (hasActiveRoleplay.value) return t('game.roleplay.status.observing')
    return ''
  })
  const requestSummary = computed(() => {
    if (isDecision.value) return t('game.roleplay.summary.decision')
    if (isChoice.value) return pending.value?.description || t('game.roleplay.summary.choice')
    if (isConversation.value) return t('game.roleplay.summary.conversation', { target: conversationTargetName.value })
    return t('game.roleplay.summary.observing')
  })
  const requestPanelTitle = computed(() => {
    if (isDecision.value) return t('game.roleplay.request.title_decision')
    if (isChoice.value) return t('game.roleplay.request.title_choice')
    if (isConversation.value) return t('game.roleplay.request.title_conversation')
    return t('game.roleplay.request.title_observing')
  })
  const requestPanelCaption = computed(() => {
    if (isDecision.value) return t('game.roleplay.request.caption_decision')
    if (isChoice.value) return t('game.roleplay.request.caption_choice')
    if (isConversation.value) return t('game.roleplay.request.caption_conversation', { avatar: avatarName.value })
    return t('game.roleplay.request.caption_observing')
  })
  const requestErrorText = computed(() => roleplayStore.error || '')
  const decisionSubmitText = computed(() => roleplayStore.isSubmitting ? t('game.roleplay.decision.submitting') : t('game.roleplay.decision.submit'))
  const choiceSubmittingText = computed(() => roleplayStore.isSubmitting ? t('game.roleplay.choice.submitting') : '')
  const conversationSubmitText = computed(() => {
    if (isConversationAwaitingReply.value) return t('game.roleplay.conversation.awaiting_reply')
    if (roleplayStore.isSubmitting) return t('game.roleplay.conversation.sending')
    return t('game.roleplay.conversation.submit')
  })

  async function refreshRoleplayState() {
    await roleplayStore.fetchSession()
  }

  async function handleSubmitDecision() {
    if (!pending.value?.request_id || !controlledAvatarId.value || !commandText.value.trim()) return
    const command = commandText.value.trim()
    optimisticInteractionRecord.value = {
      type: 'local_feedback',
      created_at: Date.now(),
      text: t('game.roleplay.feedback.decision_submitted', { text: command }),
    }
    await roleplayStore.submitDecision({
      avatar_id: controlledAvatarId.value,
      request_id: pending.value.request_id,
      command_text: command,
    })
    commandText.value = ''
  }

  async function handleSubmitChoice(selectedKey: string) {
    if (!pending.value?.request_id || !controlledAvatarId.value) return
    const selectedOption = pending.value.options?.find(option => option.key === selectedKey)
    optimisticInteractionRecord.value = {
      type: 'local_feedback',
      created_at: Date.now(),
      text: t('game.roleplay.feedback.choice_submitted', {
        text: selectedOption?.title || selectedOption?.description || selectedKey,
      }),
    }
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
      optimisticInteractionRecord.value = {
        type: 'local_feedback',
        created_at: Date.now(),
        text: t('game.roleplay.feedback.conversation_failed'),
      }
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

  watch(hasActiveRoleplay, (active) => {
    if (active) {
      startPolling()
      return
    }
    stopPolling()
    optimisticInteractionRecord.value = null
    optimisticConversationMessage.value = null
    commandText.value = ''
  })

  onMounted(() => {
    void refreshRoleplayState()
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
