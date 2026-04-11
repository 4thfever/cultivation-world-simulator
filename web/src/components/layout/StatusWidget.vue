<script setup lang="ts">
import { NPopover, NList, NListItem, NTag, NEmpty } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import type { HiddenDomainInfo } from '../../types/core'
import { formatRealmLabel } from '@/utils/cultivationText'

const { t } = useI18n()

interface Props {
  // 触发器显示
  label: string
  icon?: string
  color?: string
  
  // 弹窗内容
  title?: string
  items?: HiddenDomainInfo[] // 通用列表数据 (这里暂时专用于秘境，如果未来需要其他类型再泛型化)
  emptyText?: string
  
  // 模式: 'single' (天地灵机) 或 'list' (秘境)
  mode?: 'single' | 'list'
  
  // 是否禁用 Popover (直接点击触发)
  disablePopover?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  color: '#ccc',
  items: () => [],
  mode: 'list',
  emptyText: '',
  disablePopover: false
})

// 发射点击事件（用于天地灵机的"更易天象"）
const emit = defineEmits(['trigger-click'])

function getDomainStatClass(key: 'danger' | 'drop' | 'cooldown' | 'chance') {
  switch (key) {
    case 'danger':
      return 'is-danger'
    case 'drop':
      return 'is-drop'
    case 'cooldown':
      return 'is-cooldown'
    case 'chance':
      return 'is-chance'
  }
}
</script>

<template>
  <div class="status-widget">
    <span class="divider">|</span>
    <!-- 分支A: 禁用 Popover，直接显示 Trigger -->
    <span 
      v-if="disablePopover"
      class="widget-trigger" 
      :style="{ color: props.color }"
      @click="emit('trigger-click')"
      v-sound="'open'"
    >
      <span v-if="props.icon" class="widget-icon" :style="{ '--icon-url': `url(${props.icon})` }" aria-hidden="true"></span>
      <span>{{ props.label }}</span>
    </span>

    <!-- 分支B: 启用 Popover -->
    <n-popover v-else trigger="click" placement="bottom" style="max-width: 600px;">
      <template #trigger>
        <span 
          class="widget-trigger" 
          :style="{ color: props.color }"
          @click="emit('trigger-click')"
          v-sound="'open'"
        >
          <span v-if="props.icon" class="widget-icon" :style="{ '--icon-url': `url(${props.icon})` }" aria-hidden="true"></span>
          <span>{{ props.label }}</span>
        </span>
      </template>
      
      <!-- 弹窗内容区 -->
      <div class="widget-content">
        <!-- 模式A: 单个详情 (复用天地灵机样式) -->
        <slot name="single" v-if="mode === 'single'"></slot>

        <!-- 模式B: 列表展示 (用于秘境) -->
        <div v-else-if="mode === 'list'" class="list-container">
          <div class="list-header" v-if="title">{{ title }}</div>
          
          <n-list v-if="items.length > 0" hoverable clickable>
            <n-list-item v-for="item in items" :key="item.id">
              <div class="domain-item" :class="{ 'is-closed': !item.is_open }">
                <div class="d-header">
                  <div class="d-title-group">
                    <span class="d-name">{{ item.name }}</span>
                    <n-tag v-if="!item.is_open" size="small" :bordered="false" class="d-status closed">
                      {{ t('game.status_bar.hidden_domain.status_closed') }}
                    </n-tag>
                    <n-tag v-else size="small" :bordered="false" type="success" class="d-status open">
                      {{ t('game.status_bar.hidden_domain.status_open') }}
                    </n-tag>
                  </div>
                  <n-tag size="small" :bordered="false" type="warning" class="d-tag">
                    {{ formatRealmLabel(item.required_realm, t) }}
                  </n-tag>
                </div>
                <div class="d-desc">{{ item.desc }}</div>
                <div class="d-stats">
                  <span class="d-stat" :class="getDomainStatClass('danger')">💀 {{ (item.danger_prob * 100).toFixed(0) }}%</span>
                  <span class="d-stat" :class="getDomainStatClass('drop')">🎁 {{ (item.drop_prob * 100).toFixed(0) }}%</span>
                  <span class="d-stat" :class="getDomainStatClass('cooldown')">⏱️ {{ item.cd_years }}{{ t('common.year') }}</span>
                  <span class="d-stat" :class="getDomainStatClass('chance')">🎲 {{ (item.open_prob * 100).toFixed(0) }}%</span>
                </div>
              </div>
            </n-list-item>
          </n-list>
          <n-empty v-else :description="emptyText || t('game.status_bar.hidden_domain.empty')" class="empty-state" />
        </div>
      </div>
    </n-popover>
  </div>
</template>

<style scoped>
.widget-trigger {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: bold;
  transition: opacity 0.2s, color 0.2s;
  white-space: nowrap;
}
.widget-trigger:hover { opacity: 0.92; }
.divider { color: #4a443b; margin-right: 10px; }

.widget-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  display: inline-block;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
}

.list-header {
  font-weight: bold;
  padding: 8px 12px;
  border-bottom: 1px solid #333;
  margin-bottom: 4px;
  font-size: 14px;
  color: #ddd5c1;
}

.domain-item { 
  padding: 8px; 
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  margin-bottom: 4px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.domain-item.is-closed { 
  background: rgba(54, 46, 39, 0.22);
  border-color: rgba(130, 113, 93, 0.14);
}

.domain-item.is-closed .d-name {
  color: #9e9385;
}

.domain-item:not(.is-closed) {
  background: linear-gradient(180deg, rgba(216, 161, 74, 0.1), rgba(216, 161, 74, 0.04));
  border: 1px solid rgba(216, 161, 74, 0.18);
}

.d-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.d-title-group { display: flex; align-items: center; gap: 8px; }
.d-name { font-weight: bold; color: #dfbc72; font-size: 14px; transition: color 0.3s; }
.d-tag { font-size: 10px; height: 18px; line-height: 18px; }
.d-status { font-size: 10px; height: 18px; line-height: 18px; padding: 0 4px; }
.d-desc { 
  font-size: 12px; 
  color: #cfc8bb; 
  margin-bottom: 8px; 
  line-height: 1.4; 
}
.domain-item.is-closed .d-desc {
  color: #aaa092;
}

.d-stats { display: flex; gap: 10px; font-size: 12px; color: #9d9487; flex-wrap: wrap; }
.domain-item:not(.is-closed) .d-stats {
  color: #c8bda9;
}

.d-stat {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.d-stat.is-danger {
  color: #d48370;
}

.d-stat.is-drop {
  color: #d8b35b;
}

.d-stat.is-cooldown {
  color: #8fb0c8;
}

.d-stat.is-chance {
  color: #88bf8b;
}

.empty-state { padding: 20px; }

/* Naive UI List Override */
:deep(.n-list-item) {
  padding: 4px !important; /* 减少 list item 自身的 padding，由 domain-item 控制 */
}
:deep(.n-list-item:hover) {
  background: transparent !important; /* 避免双重 hover 背景 */
}
</style>
