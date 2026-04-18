<script setup lang="ts">
import { computed, onUnmounted } from 'vue';

import EventStreamList from '@/components/game/EventStreamList.vue';
import RoleplayChoiceView from '@/components/game/roleplay/RoleplayChoiceView.vue';
import RoleplayConversationView from '@/components/game/roleplay/RoleplayConversationView.vue';
import RoleplayDecisionView from '@/components/game/roleplay/RoleplayDecisionView.vue';
import RoleplayDockHeader from '@/components/game/roleplay/RoleplayDockHeader.vue';
import RoleplayIdleView from '@/components/game/roleplay/RoleplayIdleView.vue';
import RoleplaySectionHeader from '@/components/game/roleplay/RoleplaySectionHeader.vue';
import { useDockResize } from '@/composables/useDockResize';
import { useRoleplayDockState } from '@/composables/useRoleplayDockState';

const MIN_DOCK_HEIGHT = 148;
const MAX_DOCK_HEIGHT = 420;

const {
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
} = useRoleplayDockState();

const {
  dockHeight,
  isResizing,
  startResize,
  stopResize,
} = useDockResize(214, MIN_DOCK_HEIGHT, MAX_DOCK_HEIGHT, () => hasActiveRoleplay.value);

const dockStyle = computed(() => ({
  height: hasActiveRoleplay.value ? `${dockHeight.value}px` : '0px',
}));

onUnmounted(() => {
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

      <RoleplayDockHeader
        :avatar-name="avatarName"
        :status-text="statusText"
        :request-summary="requestSummary"
        :is-submitting="roleplayStore.isSubmitting"
        @exit="handleStopRoleplay"
      />

      <div class="roleplay-dock__body">
        <div class="roleplay-dock__main" :class="mainLayoutClass">
          <section class="roleplay-dock__active-request">
            <RoleplaySectionHeader :title="requestPanelTitle" :caption="requestPanelCaption" />

            <RoleplayDecisionView
              v-if="isDecision"
              v-model="commandText"
              :description="pending?.description || '输入一句意图，系统会把它扩展成该角色的下一步行动链。'"
              :error-text="requestErrorText"
              :is-submitting="roleplayStore.isSubmitting"
              :submit-text="decisionSubmitText"
              :interaction-history="interactionHistory"
              @submit="handleSubmitDecision"
            />

            <RoleplayChoiceView
              v-else-if="isChoice"
              :description="pending?.description || '请选择一个回应。'"
              :options="pending?.options ?? []"
              :error-text="requestErrorText"
              :is-submitting="roleplayStore.isSubmitting"
              :submitting-text="choiceSubmittingText"
              :interaction-history="interactionHistory"
              @submit="handleSubmitChoice"
            />

            <RoleplayConversationView
              v-else-if="isConversation"
              v-model="commandText"
              :avatar-name="avatarName"
              :target-name="conversationTargetName"
              :description="pending?.description || ''"
              :caption="requestPanelCaption"
              :messages="conversationMessages"
              :error-text="requestErrorText"
              :is-submitting="roleplayStore.isSubmitting"
              :submit-text="conversationSubmitText"
              :interaction-history="interactionHistory"
              @send="handleSendConversation"
              @end="handleEndConversation"
            />

            <RoleplayIdleView v-else />
          </section>

          <section class="roleplay-dock__activity-stream">
            <RoleplaySectionHeader title="事件流" caption="该角色最近发生的事" />
            <div ref="eventListRef" class="roleplay-dock__events-list">
              <EventStreamList
                :events="displayEvents"
                empty-text="暂无相关事件"
                :format-date="formatEventDate"
              />
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
.roleplay-dock__activity-stream {
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.roleplay-dock__activity-stream {
  border-left: 1px solid rgba(255, 255, 255, 0.05);
  padding-left: 10px;
}

.roleplay-dock__events-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0 4px 0 0;
}

@media (max-width: 900px) {
  .roleplay-dock__main,
  .roleplay-dock__main--conversation {
    grid-template-columns: 1fr;
  }

  .roleplay-dock__activity-stream {
    border-left: none;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    padding-left: 0;
    padding-top: 6px;
  }
}
</style>
