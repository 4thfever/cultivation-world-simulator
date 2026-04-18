<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import type { RoleplayInteractionRecordDTO } from '@/types/api'

const props = withDefaults(defineProps<{
  items: RoleplayInteractionRecordDTO[]
  maxItems?: number
}>(), {
  maxItems: 10,
})

const listRef = ref<HTMLElement | null>(null)

const visibleItems = computed(() => {
  if (props.maxItems <= 0) return props.items
  return props.items.slice(-props.maxItems)
})

watch(
  visibleItems,
  () => {
    nextTick(() => {
      const el = listRef.value
      if (!el) return
      el.scrollTop = el.scrollHeight
    })
  },
  { deep: true, immediate: true }
)
</script>

<template>
  <div v-if="visibleItems.length" ref="listRef" class="roleplay-history">
    <div
      v-for="(item, index) in visibleItems"
      :key="`${item.created_at}-${index}`"
      class="roleplay-history__row"
      :class="`roleplay-history__row--${item.type}`"
    >
      <span class="roleplay-history__marker" aria-hidden="true">
        {{
          item.type === 'command'
            ? '>'
            : item.type === 'error'
              ? '!'
              : item.type === 'choice'
                ? '?'
                : item.type === 'conversation_player'
                  ? '你'
                  : item.type === 'conversation_assistant'
                    ? '彼'
                    : item.type === 'conversation_summary'
                      ? '#'
                      : '='
        }}
      </span>
      <div class="roleplay-history__content">
        <template v-if="item.type === 'action_chain' && item.actions?.length">
          <div
            v-for="(action, actionIndex) in item.actions"
            :key="`${action.action_name}-${actionIndex}`"
            class="roleplay-history__tokens"
          >
            <span
              v-for="(token, tokenIndex) in action.tokens"
              :key="`${token.kind}-${token.text}-${tokenIndex}`"
              class="roleplay-history__token"
              :class="`roleplay-history__token--${token.kind}`"
            >
              {{ token.text }}
            </span>
          </div>
        </template>
        <span v-else>{{ item.text }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.roleplay-history {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 132px;
  overflow-y: auto;
  padding-right: 4px;
}

.roleplay-history__row {
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr);
  gap: 8px;
  align-items: start;
  font-size: 12px;
  line-height: 1.55;
  color: #d7ccb1;
}

.roleplay-history__marker {
  color: #8d7342;
}

.roleplay-history__row--error .roleplay-history__marker,
.roleplay-history__row--error .roleplay-history__content {
  color: #ff9a9a;
}

.roleplay-history__row--conversation_player .roleplay-history__marker,
.roleplay-history__row--conversation_player .roleplay-history__content {
  color: #f0dfb5;
}

.roleplay-history__row--conversation_assistant .roleplay-history__marker,
.roleplay-history__row--conversation_assistant .roleplay-history__content {
  color: #c8d6ee;
}

.roleplay-history__row--conversation_summary .roleplay-history__marker,
.roleplay-history__row--conversation_summary .roleplay-history__content {
  color: #c8ba95;
}

.roleplay-history__content {
  min-width: 0;
}

.roleplay-history__tokens {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.roleplay-history__token {
  display: inline-flex;
  align-items: center;
  min-height: 20px;
  padding: 0 7px;
  border-radius: 999px;
  font-size: 12px;
  white-space: nowrap;
}

.roleplay-history__token--verb {
  color: #f6e5c1;
  background: rgba(101, 74, 25, 0.78);
  border: 1px solid rgba(212, 179, 112, 0.22);
}

.roleplay-history__token--arg {
  color: #d7ccb1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
</style>
