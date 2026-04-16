<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';

import { useRoleplayStore } from '@/stores/roleplay';

const roleplayStore = useRoleplayStore();
const commandText = ref('');
let pollTimer: ReturnType<typeof setInterval> | null = null;

const session = computed(() => roleplayStore.session);
const pending = computed(() => session.value.pending_request);
const visible = computed(() => {
  return session.value.status === 'awaiting_decision' || session.value.status === 'awaiting_choice';
});
const avatarName = computed(() => {
  const context = session.value.last_prompt_context ?? {};
  const rawName = typeof context.avatar_name === 'string' ? context.avatar_name : '';
  return rawName || session.value.controlled_avatar_id || '角色';
});
const isDecision = computed(() => pending.value?.type === 'decision');
const isChoice = computed(() => pending.value?.type === 'choice');

async function handleSubmitDecision() {
  if (!pending.value?.request_id || !session.value.controlled_avatar_id || !commandText.value.trim()) return;
  await roleplayStore.submitDecision({
    avatar_id: session.value.controlled_avatar_id,
    request_id: pending.value.request_id,
    command_text: commandText.value.trim(),
  });
  commandText.value = '';
}

async function handleSubmitChoice(selectedKey: string) {
  if (!pending.value?.request_id || !session.value.controlled_avatar_id) return;
  await roleplayStore.submitChoice({
    avatar_id: session.value.controlled_avatar_id,
    request_id: pending.value.request_id,
    selected_key: selectedKey,
  });
}

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(() => {
    void roleplayStore.fetchSession();
  }, 1000);
}

function stopPolling() {
  if (!pollTimer) return;
  clearInterval(pollTimer);
  pollTimer = null;
}

onMounted(() => {
  void roleplayStore.fetchSession();
  startPolling();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<template>
  <div v-if="visible" class="roleplay-overlay">
    <div class="roleplay-overlay__card">
      <div class="roleplay-overlay__eyebrow">世界已暂停</div>
      <div class="roleplay-overlay__title">{{ avatarName }} 正在等待你的操作</div>
      <div class="roleplay-overlay__desc">
        {{ pending?.description || '请完成当前角色请求后，世界才会继续推进。' }}
      </div>

      <div v-if="isDecision" class="roleplay-overlay__console">
        <textarea
          v-model="commandText"
          class="roleplay-overlay__textarea"
          rows="3"
          placeholder="输入角色的下一步意图，例如：先调息恢复，再去附近探索。"
        />
        <div class="roleplay-overlay__footer">
          <div v-if="roleplayStore.error" class="roleplay-overlay__error">{{ roleplayStore.error }}</div>
          <button
            class="roleplay-overlay__primary"
            :disabled="roleplayStore.isSubmitting || !commandText.trim()"
            @click="handleSubmitDecision"
          >
            提交指令
          </button>
        </div>
      </div>

      <div v-else-if="isChoice" class="roleplay-overlay__choices">
        <button
          v-for="option in pending?.options ?? []"
          :key="option.key"
          class="roleplay-overlay__choice"
          :disabled="roleplayStore.isSubmitting"
          @click="handleSubmitChoice(option.key)"
        >
          <span class="roleplay-overlay__choice-title">{{ option.title }}</span>
          <span class="roleplay-overlay__choice-desc">{{ option.description }}</span>
        </button>
        <div v-if="roleplayStore.error" class="roleplay-overlay__error">{{ roleplayStore.error }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.roleplay-overlay {
  position: fixed;
  inset: 0;
  z-index: 120;
  pointer-events: none;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 72px;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.42), rgba(0, 0, 0, 0.08) 40%, rgba(0, 0, 0, 0));
}

.roleplay-overlay__card {
  width: min(620px, calc(100vw - 32px));
  pointer-events: auto;
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid rgba(226, 194, 132, 0.28);
  background: rgba(22, 16, 8, 0.94);
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.34);
}

.roleplay-overlay__eyebrow {
  font-size: 12px;
  letter-spacing: 0.08em;
  color: #d4bb84;
}

.roleplay-overlay__title {
  margin-top: 6px;
  font-size: 20px;
  font-weight: 700;
  color: #f6eed7;
}

.roleplay-overlay__desc {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.6;
  color: #d7ccb3;
}

.roleplay-overlay__console,
.roleplay-overlay__choices {
  margin-top: 14px;
}

.roleplay-overlay__textarea {
  width: 100%;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(8, 8, 8, 0.85);
  color: #f3f3f3;
  padding: 10px 12px;
  resize: vertical;
  font: inherit;
}

.roleplay-overlay__footer {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.roleplay-overlay__primary,
.roleplay-overlay__choice {
  border: 1px solid rgba(218, 188, 131, 0.42);
  background: rgba(90, 58, 20, 0.74);
  color: #f7edd5;
  border-radius: 10px;
  cursor: pointer;
}

.roleplay-overlay__primary {
  padding: 8px 14px;
}

.roleplay-overlay__choice {
  width: 100%;
  text-align: left;
  padding: 12px 14px;
  display: grid;
  gap: 4px;
  margin-top: 8px;
}

.roleplay-overlay__choice:first-child {
  margin-top: 0;
}

.roleplay-overlay__choice-title {
  font-size: 14px;
  font-weight: 700;
}

.roleplay-overlay__choice-desc {
  font-size: 12px;
  color: #d8ccb0;
  line-height: 1.5;
}

.roleplay-overlay__error {
  font-size: 12px;
  color: #ff9b9b;
}
</style>
