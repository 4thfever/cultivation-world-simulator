<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { onClickOutside } from '@vueuse/core';
import { useUiStore } from '../../../../stores/ui';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

// Sub-components
import AvatarDetailView from './AvatarDetail.vue';
import RegionDetailView from './RegionDetail.vue';
import SectDetailView from './SectDetail.vue';

const uiStore = useUiStore();
const panelRef = ref<HTMLElement | null>(null);
let lastOpenAt = 0;

// --- Component Resolution ---

const currentComponent = computed(() => {
  switch (uiStore.selectedTarget?.type) {
    case 'avatar': return AvatarDetailView;
    case 'region': return RegionDetailView;
    case 'sect': return SectDetailView;
    default: return null;
  }
});

// --- Title & Subtitle Logic ---

const title = computed(() => {
  if (uiStore.detailData) {
    return uiStore.detailData.name;
  }
  return uiStore.selectedTarget?.id || 'Detail';
});

const subTitle = computed(() => {
  if (uiStore.detailData && 'nickname' in uiStore.detailData && uiStore.detailData.nickname) {
    return `「${uiStore.detailData.nickname}」`;
  }
  return '';
});

const hasNicknameReason = computed(() => {
  return uiStore.detailData && 'nickname_reason' in uiStore.detailData && uiStore.detailData.nickname_reason;
});

const showNicknameReason = ref(false);

function toggleNicknameReason() {
  if (hasNicknameReason.value) {
    showNicknameReason.value = !showNicknameReason.value;
  }
}

// --- Interaction ---

function close() {
  uiStore.clearSelection();
  showNicknameReason.value = false;
}

// 使用 vueuse 的 onClickOutside 替代原生监听
onClickOutside(panelRef, () => {
  // Prevent closing immediately after opening if click propagated
  const now = performance.now();
  if (now - lastOpenAt < 100) return;
  
  close();
});

// Record open time to prevent immediate close
watch(() => uiStore.selectedTarget, (val) => {
  if (val) lastOpenAt = performance.now();
  showNicknameReason.value = false;
});
</script>

<template>
  <div v-if="uiStore.selectedTarget" class="info-panel" ref="panelRef" @wheel.stop>
    <!-- Header -->
    <div class="panel-header">
      <div class="title-group">
        <div class="main-title">{{ title }}</div>
        <div 
          v-if="subTitle" 
          class="sub-title" 
          :class="{ 'clickable': hasNicknameReason }"
          @click="toggleNicknameReason"
        >
          {{ subTitle }}
        </div>
        
        <!-- Nickname Reason Popover -->
        <div v-if="showNicknameReason && hasNicknameReason" class="nickname-reason-popover">
          <div class="popover-arrow"></div>
          <div class="popover-content">
            {{ uiStore.detailData.nickname_reason }}
          </div>
        </div>
      </div>
      <button class="close-btn" @click="close">×</button>
    </div>

    <!-- Body -->
    <div class="panel-body">
      <div v-if="uiStore.isLoadingDetail && !uiStore.detailData" class="state-msg">
        {{ t('common.loading') }}
      </div>
      
      <div v-else-if="uiStore.detailError" class="state-msg error">
        {{ uiStore.detailError }}
      </div>

      <div v-else-if="uiStore.detailData && currentComponent" class="content-wrapper">
        <component 
          :is="currentComponent" 
          :data="uiStore.detailData" 
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.info-panel {
  position: absolute;
  top: 60px;
  right: 20px;
  width: 320px;
  max-height: calc(100vh - 80px);
  background: var(--panel-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: var(--panel-shadow);
  color: #eee;
  display: flex;
  flex-direction: column;
  z-index: 50;
  pointer-events: auto;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--panel-header-bg);
  border-bottom: 1px solid var(--color-border);
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  flex-shrink: 0;
}

.title-group {
  display: flex;
  align-items: baseline;
  gap: 8px;
  position: relative;
}

.sub-title {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.sub-title.clickable {
  cursor: pointer;
  border-bottom: 1px dashed #666;
}

.sub-title.clickable:hover {
  color: #bbb;
  border-bottom-color: #999;
}

.nickname-reason-popover {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  background: rgba(50, 50, 50, 0.98);
  border: 1px solid #555;
  border-radius: 4px;
  padding: 8px 12px;
  z-index: 100;
  width: max-content;
  max-width: 260px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  pointer-events: auto;
}

.popover-arrow {
  position: absolute;
  top: -5px;
  left: 20px;
  width: 8px;
  height: 8px;
  background: rgba(50, 50, 50, 0.98);
  border-left: 1px solid #555;
  border-top: 1px solid #555;
  transform: rotate(45deg);
}

.popover-content {
  font-size: 12px;
  color: #ccc;
  line-height: 1.4;
}

.main-title {
  font-size: 16px;
  font-weight: bold;
}

.close-btn {
  background: transparent;
  border: none;
  color: #999;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  padding: 0 4px;
}

.close-btn:hover {
  color: white;
}

.panel-body {
  flex: 1;
  overflow: hidden;
  padding: 16px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.content-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.state-msg {
  color: var(--color-text-secondary);
  font-size: 13px;
  text-align: center;
  padding: 20px 0;
}

.state-msg.error {
  color: #ff7875;
}
</style>
