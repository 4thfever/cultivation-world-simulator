<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue';
import { useUiStore } from '@/stores/ui';
import type { AvatarDetail, RegionDetail } from '@/types/core';

// Sub-components
import AvatarDetailView from './AvatarDetail.vue';
import RegionDetailView from './RegionDetail.vue';

const uiStore = useUiStore();
const panelRef = ref<HTMLElement | null>(null);
let lastOpenAt = 0;

// --- Computed ---

const currentComponent = computed(() => {
  if (uiStore.selectedTarget?.type === 'avatar') return AvatarDetailView;
  if (uiStore.selectedTarget?.type === 'region') return RegionDetailView;
  return null;
});

const title = computed(() => {
  if (uiStore.detailData) {
    return uiStore.detailData.name;
  }
  return uiStore.selectedTarget?.id || 'Detail';
});

const subTitle = computed(() => {
  if (uiStore.detailData && 'nickname' in uiStore.detailData) {
    return uiStore.detailData.nickname;
  }
  return '';
});

// --- Interaction ---

function close() {
  uiStore.clearSelection();
}

  // Click outside to close
  function handleDocumentPointerDown(event: PointerEvent) {
    if (!uiStore.selectedTarget || !panelRef.value) return;
    const target = event.target as Node | null;
    
    // 检查点击是否在面板内部，或者是在二级弹窗内部（如果二级弹窗是挂在 body 上的 portal 这里的逻辑会有问题，但目前 SecondaryPopup 是 AvatarDetail 的子组件，所以应该被 panelRef 包含）
    // 但是要注意，SecondaryPopup 使用了 absolute 定位到 left: -100%，仍然是 panelRef 的子节点
    if (target && panelRef.value.contains(target)) return;

    // Prevent closing immediately after opening if click propagated
    const now = performance.now();
    if (now - lastOpenAt < 100) return;

    close();
  }

// Record open time
watch(() => uiStore.selectedTarget, (val) => {
  if (val) lastOpenAt = performance.now();
});

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown);
});

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown);
});
</script>

<template>
  <div v-if="uiStore.selectedTarget" class="info-panel" ref="panelRef" @wheel.stop>
    <!-- Header -->
    <div class="panel-header">
      <div class="title-group">
        <div class="main-title">{{ title }}</div>
        <div v-if="subTitle" class="sub-title">{{ subTitle }}</div>
      </div>
      <button class="close-btn" @click="close">×</button>
    </div>

    <!-- Body -->
    <div class="panel-body">
      <div v-if="uiStore.isLoadingDetail && !uiStore.detailData" class="state-msg">
        加载中...
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

      <!-- Fallback / Legacy Hover Info (If detail failed or not applicable) -->
      <div v-else class="legacy-list">
        <div v-for="(line, i) in uiStore.hoverInfo" :key="i" class="line">
          <span 
            v-for="(seg, j) in line" 
            :key="j"
            :style="{ color: seg.color }"
          >{{ seg.text }}</span>
        </div>
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
  background: rgba(24, 24, 24, 0.96);
  border: 1px solid #333;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45);
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
  background: rgba(38, 38, 38, 0.95);
  border-bottom: 1px solid #333;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  flex-shrink: 0;
}

.title-group {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.main-title {
  font-size: 16px;
  font-weight: bold;
}

.sub-title {
  font-size: 12px;
  color: #888;
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
  overflow: hidden; /* Let children scroll */
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
  color: #888;
  font-size: 13px;
  text-align: center;
  padding: 20px 0;
}

.state-msg.error {
  color: #ff7875;
}

/* Scrollbar Styling */
.panel-body::-webkit-scrollbar {
  width: 6px;
}

.panel-body::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.panel-body::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 3px;
}

.panel-body::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Legacy */
.legacy-list {
  font-size: 13px;
  line-height: 1.5;
}

.line {
  margin-bottom: 4px;
  white-space: pre-wrap;
}
</style>

