<script setup lang="ts">
import { NPopover, NList, NListItem, NTag, NEmpty } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import type { HiddenDomainInfo } from '../../types/core'

const { t } = useI18n()

interface Props {
  // 触发器显示
  label: string
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
  emptyText: '暂无数据',
  disablePopover: false
})

// 发射点击事件（用于天地灵机的"更易天象"）
const emit = defineEmits(['trigger-click'])
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
      {{ props.label }}
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
          {{ props.label }}
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
                    {{ item.required_realm }}
                  </n-tag>
                </div>
                <div class="d-desc">{{ item.desc }}</div>
                <div class="d-stats">
                  <span>💀 {{ (item.danger_prob * 100).toFixed(0) }}%</span>
                  <span>🎁 {{ (item.drop_prob * 100).toFixed(0) }}%</span>
                  <span>⏱️ {{ item.cd_years }}{{ t('common.year') }}</span>
                  <span>🎲 {{ (item.open_prob * 100).toFixed(0) }}%</span>
                </div>
              </div>
            </n-list-item>
          </n-list>
          <n-empty v-else :description="emptyText" class="empty-state" />
        </div>
      </div>
    </n-popover>
  </div>
</template>

<style scoped>
.widget-trigger {
  cursor: pointer;
  font-weight: bold;
  transition: opacity 0.2s;
}
.widget-trigger:hover { opacity: 0.8; }
.divider { color: #444; margin-right: 10px; }

.list-header {
  font-weight: bold;
  padding: 8px 12px;
  border-bottom: 1px solid #333;
  margin-bottom: 4px;
  font-size: 14px;
}

.domain-item { 
  padding: 8px; 
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.03);
  margin-bottom: 4px;
}

/* 移除之前的 opacity 和 grayscale，改用颜色控制 */
.domain-item.is-closed { 
  background: rgba(0, 0, 0, 0.2); 
}

/* 未开启时的标题颜色变暗 */
.domain-item.is-closed .d-name {
  color: #888;
}

/* 开启时背景稍微亮一点 */
.domain-item:not(.is-closed) {
  background: rgba(250, 219, 20, 0.05); /* 淡淡的金色背景 */
  border: 1px solid rgba(250, 219, 20, 0.1);
}

.d-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.d-title-group { display: flex; align-items: center; gap: 8px; }
.d-name { font-weight: bold; color: #fadb14; font-size: 14px; transition: color 0.3s; }
.d-tag { font-size: 10px; height: 18px; line-height: 18px; }
.d-status { font-size: 10px; height: 18px; line-height: 18px; padding: 0 4px; }
/* 描述文字颜色调整，未开启时不要太暗 */
.d-desc { 
  font-size: 12px; 
  color: #ccc; 
  margin-bottom: 8px; 
  line-height: 1.4; 
}
.domain-item.is-closed .d-desc {
  color: #999;
}

.d-stats { display: flex; gap: 12px; font-size: 12px; color: #888; flex-wrap: wrap; }
/* 统计数据在开启状态下高亮一点 */
.domain-item:not(.is-closed) .d-stats {
  color: #aaa;
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