<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import RoleplayChoiceView from '@/components/game/roleplay/RoleplayChoiceView.vue';
import RoleplayConversationView from '@/components/game/roleplay/RoleplayConversationView.vue';
import RoleplayDecisionView from '@/components/game/roleplay/RoleplayDecisionView.vue';
import RoleplayDockHeader from '@/components/game/roleplay/RoleplayDockHeader.vue';
import RoleplayIdleView from '@/components/game/roleplay/RoleplayIdleView.vue';
import RoleplayInteractionHistory from '@/components/game/roleplay/RoleplayInteractionHistory.vue';
import RoleplaySectionHeader from '@/components/game/roleplay/RoleplaySectionHeader.vue';
import { useDockResize } from '@/composables/useDockResize';
import { useRoleplayDockState } from '@/composables/useRoleplayDockState';

const MIN_DOCK_HEIGHT = 148;
const MAX_DOCK_HEIGHT = 420;
const COLLAPSED_DOCK_HEIGHT = 35;
const DOCK_HEIGHT_STORAGE_KEY = 'cws-roleplay-dock-height';
const { t } = useI18n();

const {
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
} = useRoleplayDockState();

function getInitialDockHeight() {
  const rawValue = window.localStorage.getItem(DOCK_HEIGHT_STORAGE_KEY);
  const storedHeight = rawValue ? Number(rawValue) : Number.NaN;
  if (Number.isFinite(storedHeight)) {
    return Math.max(MIN_DOCK_HEIGHT, Math.min(MAX_DOCK_HEIGHT, storedHeight));
  }
  return 214;
}

const isCollapsed = ref(false);

const {
  dockHeight,
  isResizing,
  startResize,
  stopResize,
} = useDockResize(getInitialDockHeight(), MIN_DOCK_HEIGHT, MAX_DOCK_HEIGHT, () => hasActiveRoleplay.value && !isCollapsed.value);

const dockStyle = computed(() => ({
  height: hasActiveRoleplay.value ? `${isCollapsed.value ? COLLAPSED_DOCK_HEIGHT : dockHeight.value}px` : '0px',
}));

function toggleCollapsed() {
  isCollapsed.value = !isCollapsed.value;
}

watch(dockHeight, (height) => {
  window.localStorage.setItem(DOCK_HEIGHT_STORAGE_KEY, String(height));
});

watch(hasActiveRoleplay, (active) => {
  if (active) return;
  isCollapsed.value = false;
});

onUnmounted(() => {
  stopResize();
});
</script>

<template>
  <section
    class="roleplay-dock"
    tabindex="-1"
    :class="{ 'roleplay-dock--active': hasActiveRoleplay, 'is-resizing': isResizing }"
    :style="dockStyle"
  >
    <template v-if="hasActiveRoleplay">
      <div
        class="roleplay-dock__resize-handle"
        :class="{ 'is-resizing': isResizing }"
        @mousedown="startResize"
      ></div>

      <RoleplayDockHeader
        :avatar-name="avatarName"
        :status-text="statusText"
        :request-summary="requestSummary"
        :is-submitting="roleplayStore.isSubmitting"
        :is-collapsed="isCollapsed"
        @toggle-collapse="toggleCollapsed"
        @exit="handleStopRoleplay"
      />

      <div v-if="!isCollapsed" class="roleplay-dock__body">
        <div class="roleplay-dock__main" :class="{ 'roleplay-dock__main--conversation': isConversation }">
          <section class="roleplay-dock__active-request">
            <RoleplaySectionHeader :title="requestPanelTitle" :caption="requestPanelCaption" />

            <RoleplayDecisionView
              v-if="isDecision"
              v-model="commandText"
              :description="pending?.description || t('game.roleplay.request.decision_default_description')"
              :error-text="requestErrorText"
              :is-submitting="roleplayStore.isSubmitting"
              :submit-text="decisionSubmitText"
              @submit="handleSubmitDecision"
            />

            <RoleplayChoiceView
              v-else-if="isChoice"
              :description="pending?.description || t('game.roleplay.request.choice_default_description')"
              :options="pending?.options ?? []"
              :error-text="requestErrorText"
              :is-submitting="roleplayStore.isSubmitting"
              :submitting-text="choiceSubmittingText"
              @submit="handleSubmitChoice"
            />

            <RoleplayConversationView
              v-else-if="isConversation"
              v-model="commandText"
              :avatar-name="avatarName"
              :target-name="conversationTargetName"
              :description="pending?.description || t('game.roleplay.request.conversation_default_description')"
              :caption="requestPanelCaption"
              :messages="conversationMessages"
              :error-text="requestErrorText"
              :is-submitting="roleplayStore.isSubmitting || isConversationAwaitingReply"
              :submit-text="conversationSubmitText"
              @send="handleSendConversation"
              @end="handleEndConversation"
            />

            <RoleplayIdleView v-else />
          </section>

          <section class="roleplay-dock__interaction-pane">
            <RoleplaySectionHeader :title="t('game.roleplay.dock.interaction_title')" :caption="t('game.roleplay.dock.interaction_caption')" />
            <RoleplayInteractionHistory
              v-if="interactionHistory.length"
              class="roleplay-dock__interaction-stream"
              :items="interactionHistory"
              :max-items="16"
              :player-name="avatarName"
              :counterpart-name="conversationTargetName"
              fill-height
            />
            <div v-else class="roleplay-dock__interaction-empty">
              {{ t('game.roleplay.dock.interaction_empty') }}
            </div>
          </section>
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

.roleplay-dock__body {
  height: calc(100% - 35px);
  padding: 6px 12px 8px;
}

.roleplay-dock__main {
  height: 100%;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(320px, 1.2fr) minmax(260px, 1fr);
  gap: 10px;
}

.roleplay-dock__main--conversation {
  grid-template-columns: minmax(420px, 1.8fr) minmax(240px, 1fr);
}

.roleplay-dock__active-request,
.roleplay-dock__interaction-pane {
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.roleplay-dock__interaction-pane {
  border-left: 1px solid rgba(255, 255, 255, 0.05);
  padding-left: 10px;
}

.roleplay-dock__interaction-stream {
  flex: 1;
  min-height: 0;
}

.roleplay-dock__interaction-empty {
  font-size: 12px;
  line-height: 1.55;
  color: #8e8574;
  padding-top: 6px;
}

@media (max-width: 900px) {
  .roleplay-dock__main,
  .roleplay-dock__main--conversation {
    grid-template-columns: 1fr;
  }

  .roleplay-dock__interaction-pane {
    border-left: none;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    padding-left: 0;
    padding-top: 6px;
  }
}
</style>
