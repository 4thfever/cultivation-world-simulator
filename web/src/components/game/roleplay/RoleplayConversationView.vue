<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

type ConversationMessage = {
  id: string
  role: string
  speaker_name: string
  content: string
  created_at: number
}

const props = defineProps<{
  avatarName: string
  targetName: string
  description: string
  caption: string
  modelValue: string
  messages: ConversationMessage[]
  errorText: string
  isSubmitting: boolean
  submitText: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: []
  end: []
}>()

const { t } = useI18n()

const chatListRef = ref<HTMLElement | null>(null)

function handleInput(event: Event) {
  emit('update:modelValue', (event.target as HTMLTextAreaElement).value)
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey || props.isSubmitting || !props.modelValue.trim()) return
  event.preventDefault()
  emit('send')
}

function handleSend() {
  if (props.isSubmitting || !props.modelValue.trim()) return
  emit('send')
}

watch(
  () => props.messages,
  () => {
    nextTick(() => {
      if (chatListRef.value) {
        chatListRef.value.scrollTop = chatListRef.value.scrollHeight
      }
    })
  },
  { deep: true }
)
</script>

<template>
  <div class="roleplay-dock__conversation">
    <div class="roleplay-dock__conversation-head">
      <div class="roleplay-dock__conversation-summary">
        <span class="roleplay-dock__conversation-title">{{ avatarName }} ↔ {{ targetName }}</span>
        <span class="roleplay-dock__conversation-subtitle">{{ description || caption }}</span>
      </div>
      <button
        class="roleplay-dock__submit roleplay-dock__submit--quiet"
        :disabled="isSubmitting"
        @click="emit('end')"
      >
        {{ t('game.roleplay.conversation.end') }}
      </button>
    </div>
    <div ref="chatListRef" class="roleplay-dock__chat-list">
      <div
        v-for="message in messages"
        :key="message.id"
        class="roleplay-dock__chat-line"
        :class="message.role === 'player' ? 'roleplay-dock__chat-line--player' : 'roleplay-dock__chat-line--assistant'"
      >
        <div class="roleplay-dock__chat-speaker">{{ message.speaker_name }}</div>
        <div class="roleplay-dock__chat-bubble">{{ message.content }}</div>
      </div>
    </div>
    <div class="roleplay-dock__actions roleplay-dock__actions--conversation">
      <textarea
        class="roleplay-dock__input roleplay-dock__input--conversation"
        rows="2"
        :placeholder="t('game.roleplay.conversation.placeholder')"
        :value="modelValue"
        @input="handleInput"
        @keydown="handleKeydown"
      />
      <div class="roleplay-dock__conversation-actions">
        <div v-if="errorText" class="roleplay-dock__error">{{ errorText }}</div>
        <button
          class="roleplay-dock__submit"
          :disabled="isSubmitting || !modelValue.trim()"
          @click="handleSend"
        >
          <span v-if="isSubmitting" class="roleplay-dock__spinner" aria-hidden="true"></span>
          {{ submitText }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.roleplay-dock__conversation {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-height: 0;
}

.roleplay-dock__conversation-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.roleplay-dock__conversation-summary {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.roleplay-dock__conversation-title {
  font-size: 12px;
  color: #ece0c4;
  font-weight: 700;
}

.roleplay-dock__conversation-subtitle {
  font-size: 11px;
  color: #9f957f;
}

.roleplay-dock__chat-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 4px;
}

.roleplay-dock__chat-line {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.roleplay-dock__chat-line--player {
  align-items: flex-end;
}

.roleplay-dock__chat-line--assistant {
  align-items: flex-start;
}

.roleplay-dock__chat-speaker {
  font-size: 11px;
  color: #9d927f;
}

.roleplay-dock__chat-bubble {
  max-width: min(72%, 620px);
  border-radius: 10px;
  padding: 7px 9px;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  background: rgba(255, 255, 255, 0.06);
  color: #ece5d7;
}

.roleplay-dock__chat-line--player .roleplay-dock__chat-bubble {
  background: rgba(106, 74, 26, 0.92);
}

.roleplay-dock__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.roleplay-dock__actions--conversation {
  align-items: stretch;
}

.roleplay-dock__input {
  width: 100%;
  min-height: 72px;
  resize: none;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(4, 4, 4, 0.92);
  color: #f4f1e8;
  padding: 10px 12px;
  font: inherit;
}

.roleplay-dock__input--conversation {
  min-height: 48px;
}

.roleplay-dock__conversation-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.roleplay-dock__submit {
  border: 1px solid rgba(208, 180, 124, 0.26);
  border-radius: 8px;
  padding: 6px 10px;
  white-space: nowrap;
  font-size: 12px;
  color: #f6ecd2;
  background: rgba(86, 61, 23, 0.78);
  cursor: pointer;
}

.roleplay-dock__submit--quiet {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.15);
}

.roleplay-dock__submit:disabled {
  cursor: default;
  opacity: 0.62;
}

.roleplay-dock__error {
  font-size: 12px;
  line-height: 1.6;
  color: #ff9a9a;
}

.roleplay-dock__spinner {
  width: 12px;
  height: 12px;
  margin-right: 6px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: roleplay-dock-spin 0.7s linear infinite;
  display: inline-block;
  vertical-align: -2px;
}

@keyframes roleplay-dock-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
