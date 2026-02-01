<script setup lang="ts">
import { useWorldStore } from '../../stores/world'
import { useSocketStore } from '../../stores/socket'
import { ref, computed } from 'vue'
import { NPopover, NModal, NList, NListItem, NTag, NEmpty, useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import StatusWidget from './StatusWidget.vue'

const { t } = useI18n()
const store = useWorldStore()
const socketStore = useSocketStore()
const message = useMessage()
const showSelector = ref(false)

const phenomenonColor = computed(() => {
  const p = store.currentPhenomenon;
  if (!p) return '#ccc';
  return getRarityColor(p.rarity);
})

const domainLabel = computed(() => {
  const count = store.activeDomains.length;
  return count > 0 
    ? t('game.status_bar.hidden_domain.label_active', { count }) 
    : t('game.status_bar.hidden_domain.label');
});

const domainColor = computed(() => {
  return store.activeDomains.length > 0 ? '#fa8c16' : '#666'; // 有秘境时亮橙色，否则灰色
});

function getRarityColor(rarity: string) {
  switch (rarity) {
    case 'N': return '#ccc';
    case 'R': return '#4dabf7'; // Blue
    case 'SR': return '#a0d911'; // Lime
    case 'SSR': return '#fa8c16'; // Orange/Gold
    default: return '#ccc';
  }
}
// ...
// ...
</script>

<template>
  <header class="top-bar">
    <div class="left">
      <span class="title">{{ t('splash.title') }}</span>
      <span class="status-dot" :class="{ connected: socketStore.isConnected }"></span>
    </div>
    <div class="center">
      <span class="time">{{ store.year }}{{ t('common.year') }} {{ store.month }}{{ t('common.month') }}</span>
      
      <!-- 天地灵机 -->
      <StatusWidget 
        v-if="store.currentPhenomenon"
        :label="`[${store.currentPhenomenon.name}]`"
        :color="phenomenonColor"
        mode="single"
        @trigger-click="openPhenomenonSelector"
      >
        <template #single>
          <div class="phenomenon-card">
            <div class="p-header" :style="{ color: phenomenonColor }">
              <span class="p-title">{{ store.currentPhenomenon.name }}</span>
              <span class="p-rarity">{{ store.currentPhenomenon.rarity }}</span>
            </div>
            <div class="p-desc">{{ store.currentPhenomenon.desc }}</div>
            
            <!-- 效果描述 -->
            <div class="effect-block" v-if="store.currentPhenomenon.effect_desc">
              <div class="effect-label">{{ t('game.status_bar.effect') }}</div>
              <div class="effect-content">{{ store.currentPhenomenon.effect_desc }}</div>
            </div>

            <div class="p-duration" v-if="store.currentPhenomenon.duration_years">
               {{ t('game.status_bar.duration', { years: store.currentPhenomenon.duration_years }) }}
            </div>
            <div class="click-tip">{{ t('game.status_bar.click_to_change') }}</div>
          </div>
        </template>
      </StatusWidget>

      <!-- 秘境 -->
      <StatusWidget
        :label="domainLabel"
        :color="domainColor"
        mode="list"
        :title="t('game.status_bar.hidden_domain.title')"
        :items="store.activeDomains"
        :empty-text="t('game.status_bar.hidden_domain.empty')"
      />
    </div>

    <!-- 天象选择器 Modal -->
    <n-modal
      v-model:show="showSelector"
      preset="card"
      :title="t('game.status_bar.selector_title')"
      style="width: 700px; max-height: 80vh; overflow-y: auto;"
    >
      <n-list hoverable clickable>
        <n-list-item v-for="p in store.phenomenaList" :key="p.id" @click="handleSelect(p.id, p.name)">
          <div class="list-item-content">
            <div class="item-left">
              <div class="item-name" :style="{ color: getRarityColor(p.rarity) }">
                {{ p.name }}
                <n-tag size="small" :bordered="false" :color="{ color: 'rgba(255,255,255,0.1)', textColor: getRarityColor(p.rarity) }">
                  {{ p.rarity }}
                </n-tag>
              </div>
              <div class="item-desc">{{ p.desc }}</div>
            </div>
            <div class="item-right">
               <div class="item-effect" v-if="p.effect_desc">{{ p.effect_desc }}</div>
            </div>
          </div>
        </n-list-item>
        <n-empty v-if="store.phenomenaList.length === 0" :description="t('game.status_bar.empty_data')" />
      </n-list>
    </n-modal>

    <div class="author">
      {{ t('splash.title') }}<a
        class="author-link"
        href="https://space.bilibili.com/527346837"
        target="_blank"
        rel="noopener"
      >{{ t('game.status_bar.author_bilibili') }}</a>
      <a
        class="author-link"
        href="https://github.com/4thfever/cultivation-world-simulator"
        target="_blank"
        rel="noopener"
      >
        {{ t('game.status_bar.author_github') }}
      </a>
    </div>
    <div class="right">
      <span>{{ t('game.status_bar.cultivators', { count: store.avatarList.length }) }}</span>
    </div>
  </header>
</template>

<style scoped>
.top-bar {
  height: 36px;
  background: #1f1f1f;
  border-bottom: 1px solid #333;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  font-size: 14px;
  z-index: 10;
  gap: 16px;
}

.top-bar .title {
  font-weight: bold;
  margin-right: 8px;
}

.center {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* .phenomenon, .divider, .phenomenon-name REMOVED (moved to StatusWidget) */

.phenomenon-card {
  padding: 4px 0;
}

.p-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: bold;
  font-size: 15px;
  border-bottom: 1px solid #333;
  padding-bottom: 4px;
}

.p-rarity {
  font-size: 12px;
  opacity: 0.8;
  border: 1px solid currentColor;
  padding: 0 4px;
  border-radius: 2px;
}

.p-desc {
  font-size: 13px;
  color: #ddd;
  line-height: 1.5;
  margin-bottom: 8px;
}

/* 统一的效果块样式 */
.effect-block {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid #444;
  border-radius: 4px;
  padding: 8px 10px;
  margin: 8px 0;
}

.effect-label {
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
}

.effect-content {
  font-size: 13px;
  color: #fadb14; /* 亮黄色，匹配游戏常见的高亮色 */
  font-weight: 500;
  line-height: 1.5;
  white-space: pre-wrap;
}

.p-duration {
  font-size: 12px;
  color: #888;
  text-align: right;
}

.click-tip {
  font-size: 10px;
  color: #666;
  text-align: center;
  margin-top: 8px;
  border-top: 1px dashed #333;
  padding-top: 4px;
}

.list-item-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 0;
}

.item-name {
  font-weight: bold;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-desc {
  color: #aaa;
  font-size: 13px;
}

.item-effect {
  font-size: 12px;
  color: #e6a23c; /* Warning color */
  background: rgba(230, 162, 60, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 4px;
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ff4d4f;
}

.status-dot.connected {
  background: #52c41a;
}

.author {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  color: #bbb;
  display: none; /* 暂时隐藏，因为空间可能不够 */
}

@media (min-width: 1024px) {
  .author {
    display: flex;
  }
}

.author-link {
  color: #4dabf7;
  text-decoration: none;
}

.author-link:hover {
  color: #8bc6ff;
  text-decoration: underline;
}
</style>
