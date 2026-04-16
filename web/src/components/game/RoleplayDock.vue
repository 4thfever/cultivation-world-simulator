<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';

import { eventApi } from '@/api';
import { mapEventDtosToTimeline } from '@/api/mappers/event';
import { useRoleplayStore } from '@/stores/roleplay';
import type { GameEvent } from '@/types/core';
import { logError } from '@/utils/appError';
import { useDockResize } from '@/composables/useDockResize';

const MIN_DOCK_HEIGHT = 148;
const MAX_DOCK_HEIGHT = 420;

const roleplayStore = useRoleplayStore();
const commandText = ref('');
const localEvents = ref<GameEvent[]>([]);
const eventListRef = ref<HTMLElement | null>(null);

let pollTimer: ReturnType<typeof setInterval> | null = null;

const session = computed(() => roleplayStore.session);
const pending = computed(() => session.value.pending_request);
const controlledAvatarId = computed(() => session.value.controlled_avatar_id ?? '');
const hasActiveRoleplay = computed(() => !!controlledAvatarId.value);
const isDecision = computed(() => pending.value?.type === 'decision');
const isChoice = computed(() => pending.value?.type === 'choice');
const displayEvents = computed(() => localEvents.value);
const avatarName = computed(() => {
  const context = session.value.last_prompt_context ?? {};
  const rawName = typeof context.avatar_name === 'string' ? context.avatar_name : '';
  return rawName || controlledAvatarId.value || '角色';
});
const statusText = computed(() => {
  if (session.value.status === 'awaiting_decision') return '等待指令';
  if (session.value.status === 'awaiting_choice') return '等待选择';
  if (session.value.status === 'submitting') return '提交中';
  if (hasActiveRoleplay.value) return '观察中';
  return '';
});
const decisionSubmitText = computed(() => roleplayStore.isSubmitting ? '处理中...' : '提交指令');
const choiceSubmittingText = computed(() => roleplayStore.isSubmitting ? '正在处理选择，请稍候...' : '');

const {
  dockHeight,
  isResizing,
  startResize,
  stopResize,
} = useDockResize(214, MIN_DOCK_HEIGHT, MAX_DOCK_HEIGHT, () => hasActiveRoleplay.value);

const dockStyle = computed(() => ({
  height: hasActiveRoleplay.value ? `${dockHeight.value}px` : '0px',
}));

async function refreshRoleplayState() {
  await roleplayStore.fetchSession();
}

async function refreshLocalEvents() {
  if (!controlledAvatarId.value) {
    localEvents.value = [];
    return;
  }
  try {
    const page = await eventApi.fetchEvents({ avatar_id: controlledAvatarId.value, limit: 18 });
    localEvents.value = mapEventDtosToTimeline(page.events);
  } catch (e) {
    logError('RoleplayDock refresh events', e);
  }
}

async function handleSubmitDecision() {
  if (!pending.value?.request_id || !controlledAvatarId.value || !commandText.value.trim()) return;
  await roleplayStore.submitDecision({
    avatar_id: controlledAvatarId.value,
    request_id: pending.value.request_id,
    command_text: commandText.value.trim(),
  });
  commandText.value = '';
}

async function handleSubmitChoice(selectedKey: string) {
  if (!pending.value?.request_id || !controlledAvatarId.value) return;
  await roleplayStore.submitChoice({
    avatar_id: controlledAvatarId.value,
    request_id: pending.value.request_id,
    selected_key: selectedKey,
  });
}

async function handleStopRoleplay() {
  if (!controlledAvatarId.value) return;
  await roleplayStore.stopRoleplay(controlledAvatarId.value);
}

function getChoiceVariant(option: { key?: string; title?: string }): 'accept' | 'reject' | 'default' {
  const content = `${option.key ?? ''} ${option.title ?? ''}`.toLowerCase();
  if (
    content.includes('accept') ||
    content.includes('agree') ||
    content.includes('yes') ||
    content.includes('take') ||
    content.includes('接受') ||
    content.includes('同意') ||
    content.includes('采纳') ||
    content.includes('答应')
  ) {
    return 'accept';
  }
  if (
    content.includes('reject') ||
    content.includes('decline') ||
    content.includes('refuse') ||
    content.includes('no') ||
    content.includes('拒绝') ||
    content.includes('放弃') ||
    content.includes('不')
  ) {
    return 'reject';
  }
  return 'default';
}

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(() => {
    void refreshRoleplayState();
    void refreshLocalEvents();
  }, 1000);
}

function stopPolling() {
  if (!pollTimer) return;
  clearInterval(pollTimer);
  pollTimer = null;
}

watch(controlledAvatarId, () => {
  void refreshLocalEvents();
});

watch(displayEvents, () => {
  const el = eventListRef.value;
  if (!el) return;

  const isScrollable = el.scrollHeight > el.clientHeight;
  const isAtBottom = !isScrollable || (el.scrollHeight - el.scrollTop - el.clientHeight < 50);

  if (isAtBottom) {
    nextTick(() => {
      if (eventListRef.value) {
        eventListRef.value.scrollTop = eventListRef.value.scrollHeight;
      }
    });
  }
}, { deep: true });

onMounted(() => {
  void refreshRoleplayState();
  void refreshLocalEvents();
  startPolling();
});

onUnmounted(() => {
  stopPolling();
  stopResize();
});
</script>

<template>
  <section
    class="roleplay-dock"
    :class="{ 'roleplay-dock--active': hasActiveRoleplay, 'is-resizing': isResizing }"
    :style="dockStyle"
  >
    <template v-if="hasActiveRoleplay">
      <div
        class="roleplay-dock__resize-handle"
        :class="{ 'is-resizing': isResizing }"
        @mousedown="startResize"
      ></div>

      <div class="roleplay-dock__toolbar">
        <div class="roleplay-dock__meta">
          <span class="roleplay-dock__avatar">{{ avatarName }}</span>
          <span class="roleplay-dock__status">{{ statusText }}</span>
          <span v-if="pending?.description" class="roleplay-dock__notice">{{ pending.description }}</span>
        </div>
        <button
          class="roleplay-dock__exit"
          :disabled="roleplayStore.isSubmitting"
          @click="handleStopRoleplay"
        >
          退出扮演
        </button>
      </div>

      <div class="roleplay-dock__body">
        <div v-if="isDecision" class="roleplay-dock__console">
          <textarea
            v-model="commandText"
            class="roleplay-dock__input"
            rows="3"
            placeholder="输入角色的下一步意图，例如：先调息恢复，再去附近探索。"
          />
          <div class="roleplay-dock__actions">
            <div v-if="roleplayStore.error" class="roleplay-dock__error">{{ roleplayStore.error }}</div>
            <button
              class="roleplay-dock__submit"
              :disabled="roleplayStore.isSubmitting || !commandText.trim()"
              @click="handleSubmitDecision"
            >
              {{ decisionSubmitText }}
            </button>
          </div>
        </div>

        <div v-else-if="isChoice" class="roleplay-dock__choice-list">
          <button
            v-for="option in pending?.options ?? []"
            :key="option.key"
            class="roleplay-dock__choice"
            :class="`roleplay-dock__choice--${getChoiceVariant(option)}`"
            :disabled="roleplayStore.isSubmitting"
            @click="handleSubmitChoice(option.key)"
          >
            <span class="roleplay-dock__choice-title">{{ option.title }}</span>
            <span class="roleplay-dock__choice-desc">{{ option.description }}</span>
          </button>
          <div v-if="choiceSubmittingText" class="roleplay-dock__submitting-hint">{{ choiceSubmittingText }}</div>
          <div v-if="roleplayStore.error" class="roleplay-dock__error">{{ roleplayStore.error }}</div>
        </div>

        <div v-else class="roleplay-dock__idle">
          当前仍在上帝视角观察世界。该角色的动作链结束后，会在这里等待你的下一步操作。
        </div>

      <div class="roleplay-dock__events">
          <div ref="eventListRef" class="roleplay-dock__events-list">
            <div v-if="displayEvents.length === 0" class="roleplay-dock__events-empty">暂无相关事件</div>
            <div v-for="event in displayEvents" :key="event.id" class="roleplay-dock__event-line">
              <span class="roleplay-dock__event-time">{{ event.year }}年{{ event.month }}月</span>
              <span class="roleplay-dock__event-text">{{ event.content || event.text }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.roleplay-dock {
  position: relative;
  flex-shrink: 0;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(96, 70, 28, 0.12), rgba(10, 10, 10, 0) 18%),
    rgba(10, 10, 10, 0.96);
  transition: height 0.18s ease;
}

.roleplay-dock--active {
  border-top: 1px solid rgba(204, 173, 114, 0.24);
}

.roleplay-dock.is-resizing {
  transition: none;
}

.roleplay-dock__resize-handle {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 6px;
  cursor: row-resize;
  z-index: 2;
  background: transparent;
  transition: background 0.15s;
}

.roleplay-dock__resize-handle.is-resizing,
.roleplay-dock__resize-handle:hover {
  background: rgba(85, 85, 85, 0.9);
}

.roleplay-dock__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 34px;
  padding: 8px 14px 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.roleplay-dock__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-size: 12px;
}

.roleplay-dock__avatar {
  font-size: 15px;
  font-weight: 700;
  color: #f4efe2;
  white-space: nowrap;
}

.roleplay-dock__status {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(110, 79, 29, 0.35);
  border: 1px solid rgba(212, 185, 133, 0.24);
  color: #dfcca4;
  font-size: 11px;
}

.roleplay-dock__notice {
  min-width: 0;
  color: #cfc3a9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.roleplay-dock__exit,
.roleplay-dock__submit,
.roleplay-dock__choice {
  border: 1px solid rgba(208, 180, 124, 0.26);
  color: #f6ecd2;
  background: rgba(86, 61, 23, 0.78);
  cursor: pointer;
}

.roleplay-dock__exit,
.roleplay-dock__submit {
  border-radius: 8px;
  padding: 7px 11px;
  white-space: nowrap;
  font-size: 12px;
}

.roleplay-dock__body {
  height: calc(100% - 35px);
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 14px 10px;
}

.roleplay-dock__console {
  display: flex;
  flex-direction: column;
  gap: 8px;
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

.roleplay-dock__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.roleplay-dock__choice-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  align-items: stretch;
  width: 100%;
  max-width: 680px;
  margin: 0 auto;
}

.roleplay-dock__choice {
  flex: 1 1 220px;
  max-width: 320px;
  min-height: 68px;
  border-radius: 8px;
  padding: 8px 10px;
  text-align: left;
  display: grid;
  gap: 3px;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.12s ease;
}

.roleplay-dock__choice:hover {
  transform: translateY(-1px);
}

.roleplay-dock__choice:active {
  transform: translateY(0);
}

.roleplay-dock__choice--accept {
  border-color: rgba(98, 190, 133, 0.42);
  background: linear-gradient(180deg, rgba(62, 116, 81, 0.56), rgba(42, 78, 56, 0.82));
}

.roleplay-dock__choice--accept:hover {
  border-color: rgba(126, 216, 160, 0.64);
  background: linear-gradient(180deg, rgba(72, 132, 92, 0.66), rgba(50, 93, 67, 0.9));
}

.roleplay-dock__choice--reject {
  border-color: rgba(213, 108, 108, 0.45);
  background: linear-gradient(180deg, rgba(130, 58, 58, 0.55), rgba(94, 42, 42, 0.82));
}

.roleplay-dock__choice--reject:hover {
  border-color: rgba(232, 140, 140, 0.64);
  background: linear-gradient(180deg, rgba(148, 66, 66, 0.66), rgba(108, 48, 48, 0.9));
}

.roleplay-dock__choice--default {
  border-color: rgba(208, 180, 124, 0.26);
  background: rgba(86, 61, 23, 0.78);
}

.roleplay-dock__choice-title {
  font-size: 12px;
  font-weight: 700;
}

.roleplay-dock__choice-desc {
  font-size: 11px;
  line-height: 1.4;
  color: #efe7d5;
}

@media (max-width: 640px) {
  .roleplay-dock__choice {
    flex-basis: 100%;
    max-width: none;
  }
}

.roleplay-dock__idle {
  font-size: 12px;
  line-height: 1.5;
  color: #cfc3a9;
}

.roleplay-dock__events {
  flex: 1;
  min-height: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 8px;
}

.roleplay-dock__events-list {
  height: 100%;
  overflow-y: auto;
  padding: 0 4px 0 0;
}

.roleplay-dock__event-line {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #2a2a2a;
}

.roleplay-dock__event-line:last-child {
  border-bottom: none;
}

.roleplay-dock__event-time {
  flex: 0 0 76px;
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.roleplay-dock__event-text,
.roleplay-dock__events-empty,
.roleplay-dock__error {
  font-size: 12px;
  line-height: 1.6;
}

.roleplay-dock__event-text {
  color: #ddd;
  flex: 1;
  min-width: 0;
}

.roleplay-dock__events-empty {
  color: #666;
  text-align: center;
  padding: 10px 0;
}

.roleplay-dock__error {
  color: #ff9a9a;
}

.roleplay-dock__submitting-hint {
  width: 100%;
  text-align: center;
  font-size: 12px;
  color: #cdb78c;
  padding: 2px 0;
}

@media (max-width: 900px) {
  .roleplay-dock__toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .roleplay-dock__meta {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
