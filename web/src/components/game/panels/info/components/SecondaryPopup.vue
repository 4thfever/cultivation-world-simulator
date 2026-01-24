<script setup lang="ts">
import type { EffectEntity } from '@/types/core';
import { getEntityColor } from '@/utils/theme';
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const props = defineProps<{
  item: EffectEntity | null;
}>();

defineEmits(['close']);

const displayType = computed(() => {
  if (props.item?.type_name) return props.item.type_name; // 优先使用后端传回的中文类型名
  if (!props.item?.type) return '';
  return t(`game.info_panel.popup.types.${props.item.type}`) || props.item.type;
});
</script>

<template>
  <Teleport to="body">
    <div v-if="item" class="secondary-panel">
      <div class="sec-header">
        <span class="sec-title" :style="{ color: getEntityColor(item) }">
          {{ item.name }}
        </span>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      
      <div class="sec-body">
        <div class="sec-row" v-if="item.grade || item.rarity || displayType">
          <span v-if="item.grade || item.rarity" class="badge grade-badge">{{ item.grade || item.rarity }}</span>
          <span v-if="displayType" class="badge type-badge">{{ displayType }}</span>
        </div>
        
        <div class="sec-desc" v-if="item.desc">{{ item.desc }}</div>
        
        <div v-if="item.effect_desc" class="effect-box">
          <div class="label">{{ t('game.info_panel.popup.effect') }}</div>
          <div class="effect-text">{{ item.effect_desc }}</div>
        </div>

        <!-- Drops Display -->
        <div v-if="item.drops?.length" class="drops-box">
          <div class="label">{{ t('game.info_panel.popup.drops') }}</div>
          <div class="drop-list">
            <span 
              v-for="drop in item.drops" 
              :key="drop.id" 
              class="drop-tag"
              :style="{ color: getEntityColor(drop) }"
            >
              {{ drop.name }}
            </span>
          </div>
        </div>
        
        <!-- 动态字段展示 (Extensibility) -->
        <div v-if="item.hq_name" class="extra-info">
          <div><strong>{{ t('game.info_panel.popup.hq') }}</strong> {{ item.hq_name }}</div>
          <div class="sub-desc">{{ item.hq_desc }}</div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.secondary-panel {
  position: fixed;
  top: 96px;       /* 36px (StatusBar) + 60px (InfoPanel top offset) */
  /* 
    计算逻辑：
    Sidebar Width: 400px (App.vue 中定义的右侧侧边栏)
    InfoPanel Margin Right: 20px (相对于 map-container 右侧)
    InfoPanel Width: 320px
    Gap: 12px
    Total Right = 400 + 20 + 320 + 12 = 752px
  */
  right: 752px;
  width: 260px;
  background: rgba(32, 32, 32, 0.98);
  border: 1px solid #555;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.8);
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #444;
  padding-bottom: 8px;
}

.sec-title {
  font-size: 15px;
  font-weight: bold;
}

.close-btn {
  background: transparent;
  border: none;
  color: #888;
  font-size: 18px;
  cursor: pointer;
  padding: 0 4px;
}

.close-btn:hover {
  color: #fff;
}

.sec-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 13px;
  color: #ccc;
}

.badge {
  display: inline-block;
  padding: 2px 6px;
  background: #444;
  border-radius: 4px;
  font-size: 11px;
  color: #fff;
}

.sec-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.grade-badge {
  background: rgba(255, 215, 0, 0.2);
  border: 1px solid rgba(255, 215, 0, 0.4);
  color: #daa520;
}

.type-badge {
  background: rgba(100, 149, 237, 0.2);
  border: 1px solid rgba(100, 149, 237, 0.4);
  color: #87ceeb;
}

.sec-desc {
  line-height: 1.5;
  color: #bbb;
}

.effect-box {
  background: rgba(0, 0, 0, 0.2);
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #444;
}

.label {
  font-size: 11px;
  color: #888;
  margin-bottom: 4px;
}

.effect-text {
  color: #ffd700;
  font-size: 12px;
  line-height: 1.4;
}

.extra-info {
  border-top: 1px solid #444;
  padding-top: 8px;
  font-size: 12px;
}

.sub-desc {
  color: #888;
  margin-top: 2px;
}

.drops-box {
  margin-top: 4px;
}

.drop-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.drop-tag {
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 11px;
}
</style>
